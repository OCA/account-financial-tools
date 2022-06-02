# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockInventoryRevaluationLine(models.Model):
    _name = "stock.inventory.revaluation.line"
    _description = "Stock inventory revaluation Line"

    name = fields.Char("Description")
    stock_inventory_revaluation_id = fields.Many2one(
        "stock.inventory.revaluation",
        "Inventory revaluation",
        ondelete="cascade",
    )

    product_id = fields.Many2one("product.product", "Product", required=True)
    account_id = fields.Many2one(
        "account.account", "Account", domain=[("deprecated", "=", False)]
    )
    currency_id = fields.Many2one(
        "res.currency", related="stock_inventory_revaluation_id.currency_id"
    )
    stock_move_id = fields.Many2one("stock.move", "Stock Move", readonly=True)
    quantity = fields.Float("Quantity", default=1.0, digits=0, required=True)
    original_value = fields.Monetary("Original Value")
    price_subtotal = fields.Monetary("Total Value", required=True, default=0.0)
    additional_value = fields.Monetary("Additional Value")
    final_value = fields.Monetary(
        "New Value", compute="_compute_final_value", store=True
    )
    used_stock_valuation_layer_ids = fields.Many2many(
        comodel_name="stock.valuation.layer",
        relation="stock_inventory_revaluation_valuation_layer_rel",
        column1="stock_inventory_revaluation_id",
        column2="valuation_layer_id",
        string="Used Layers",
        ondelete="cascade",
    )
    created_stock_valuation_layer_ids = fields.Many2many(
        comodel_name="stock.valuation.layer",
        relation="stock_inventory_revaluation_valuation_created_layer_rel",
        column1="stock_inventory_revaluation_id",
        column2="valuation_layer_id",
        string="Created Layers",
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.name = self.product_id.name or ""
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        self.account_id = accounts_data["stock_input"]

    @api.depends("revaluation_line_id.name", "product_id.code", "product_id.name")
    def _compute_name(self):
        for line in self:
            name = "%s - " % (
                line.revaluation_line_id.name if line.revaluation_line_id else ""
            )
            line.name = name + (line.product_id.code or line.product_id.name or "")

    @api.depends("original_value", "additional_value")
    def _compute_final_value(self):
        for line in self:
            line.final_value = line.original_value + line.additional_value

    def _create_accounting_entries(self, move, revaluation_line):
        revaluation_product = self.product_id
        if not revaluation_product:
            return False
        accounts = self.product_id.product_tmpl_id.get_product_accounts()
        debit_account_id = self._get_debit_account(accounts)
        credit_account_id = self._get_credit_account(revaluation_product)
        already_out_account_id = accounts["stock_output"].id

        if not credit_account_id:
            raise UserError(
                _("Please configure Stock Expense Account for product: %s.")
                % (revaluation_product.name)
            )

        return self._create_account_move_line(
            move,
            revaluation_line,
            credit_account_id,
            debit_account_id,
            already_out_account_id,
        )

    def _prepare_base_line(self, move, revaluation_line):
        base_line = {
            "name": self.name,
            "product_id": self.product_id.id,
            "stock_move_id": move.id,
            "stock_inventory_revaluation_line_id": revaluation_line.id,
            "quantity": 0,
        }
        return base_line

    def _create_account_move_line(
        self,
        move,
        revaluation_line,
        credit_account_id,
        debit_account_id,
        already_out_account_id,
    ):
        """
        Generate the account.move.line values to track the inventory revaluation.
        Afterwards, for the goods that are already out of stock, we should create
        the out moves
        """
        AccountMoveLine = []
        base_line = self._prepare_base_line(move, revaluation_line)
        debit_line = dict(base_line, account_id=debit_account_id)
        credit_line = dict(base_line, account_id=credit_account_id)
        diff = self.additional_value
        if diff > 0.0:
            debit_line["debit"] = diff
            credit_line["credit"] = diff
        else:
            # negative revaluation, reverse the entry
            debit_line["credit"] = -diff
            credit_line["debit"] = -diff
        AccountMoveLine.append([0, 0, debit_line])
        AccountMoveLine.append([0, 0, credit_line])

        self.create_account_move_line_already_out(
            AccountMoveLine, base_line, already_out_account_id, debit_account_id
        )
        return AccountMoveLine

    def _get_debit_account(self, accounts):
        debit_account_id = (
            accounts.get("stock_valuation") and accounts["stock_valuation"].id or False
        )
        return debit_account_id

    def _get_credit_account(self, revaluation_product):
        credit_account_id = (
            self.account_id.id
            or revaluation_product.categ_id.property_stock_account_input_categ_id.id
        )
        return credit_account_id

    def _get_anglosaxon_expense_account(self):
        return self.product_id.product_tmpl_id.get_product_accounts()["expense"]

    def create_output_valuation_entries(self, move_vals, move):
        self.ensure_one()
        move_vals["line_ids"] += self._create_accounting_entries(move, self)
        return move_vals

    def create_account_move_line_already_out(
        self, AccountMoveLine, base_line, already_out_account_id, debit_account_id
    ):
        # Create account move lines for quants already out of stock, except if it
        # is a revaluation of a return to supplier
        diff = self.additional_value
        # I exclude returns, considering the vendor bill is for the qty received
        # or received and delivered to customers, but never a bill for qauntity
        # returned
        for usage in self.stock_move_id.stock_valuation_layer_ids.mapped(
            "usage_ids"
        ).filtered(lambda l: l.stock_move_id.location_dest_id.usage == "customer"):
            qty_out = usage.quantity
            if qty_out > 0:
                # TODO: move this to a method out of here
                debit_line = dict(
                    base_line,
                    name=(self.name + ": " + str(qty_out) + _(" already out")),
                    quantity=0,
                    account_id=already_out_account_id,
                )
                credit_line = dict(
                    base_line,
                    name=(self.name + ": " + str(qty_out) + _(" already out")),
                    quantity=0,
                    account_id=debit_account_id,
                )
                diff = diff * qty_out / self.quantity
                if diff > 0.0:
                    debit_line["debit"] = diff
                    credit_line["credit"] = diff
                else:
                    # negative revaluation, reverse the entry
                    debit_line["credit"] = -diff
                    credit_line["debit"] = -diff
                AccountMoveLine.append([0, 0, debit_line])
                AccountMoveLine.append([0, 0, credit_line])

                if self.env.company.anglo_saxon_accounting:
                    expense_account = self._get_anglosaxon_expense_account()
                    expense_account_id = expense_account.id
                    debit_line = dict(
                        base_line,
                        name=(self.name + ": " + str(qty_out) + _(" already out")),
                        quantity=0,
                        account_id=expense_account_id,
                    )
                    credit_line = dict(
                        base_line,
                        name=(self.name + ": " + str(qty_out) + _(" already out")),
                        quantity=0,
                        account_id=already_out_account_id,
                    )

                    if diff > 0.0:
                        debit_line["debit"] = diff
                        credit_line["credit"] = diff
                    else:
                        # negative revaluation, reverse the entry
                        debit_line["credit"] = -diff
                        credit_line["debit"] = -diff
                    AccountMoveLine.append([0, 0, debit_line])
                    AccountMoveLine.append([0, 0, credit_line])
        return AccountMoveLine
