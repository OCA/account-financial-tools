# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.osv import expression
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    _inherit = "sale.order"

    unreconciled = fields.Boolean(
        compute="_compute_unreconciled",
        search="_search_unreconciled",
        help="""Indicates that a sale Order has related Journal items not
             reconciled.Note that if it is false it can be either that
             everything is reconciled or that the related accounts do not
             allow reconciliation""",
        compute_sudo=True,
    )
    amount_unreconciled = fields.Float(
        compute="_compute_unreconciled", compute_sudo=True
    )

    def _get_account_domain(self):
        self.ensure_one()
        included_accounts = (
            (
                self.env["product.category"]
                .with_company(self.company_id.id)
                .search([("property_valuation", "=", "real_time")])
            )
            .mapped("property_stock_account_output_categ_id")
            .ids
        )
        return [("account_id", "in", included_accounts)]

    @api.model
    def _get_sale_unreconciled_base_domain(self):
        unreconciled_domain = [
            ("account_id.reconcile", "=", True),
            ("account_id.internal_type", "not in", ["receivable", "payable"]),
            ("move_id.state", "=", "posted"),
            # same condition than Odoo Unreconciled filter
            ("full_reconcile_id", "=", False),
            ("balance", "!=", 0.0),
        ]
        return unreconciled_domain

    def _compute_unreconciled(self):
        acc_item = self.env["account.move.line"]
        for rec in self:
            domain = rec.with_company(
                rec.company_id
            )._get_sale_unreconciled_base_domain()
            domain_account = rec._get_account_domain()
            unreconciled_domain = expression.AND([domain, domain_account])
            unreconciled_domain = expression.AND(
                [unreconciled_domain, [("sale_order_id", "=", rec.id)]]
            )
            unreconciled_items = acc_item.search(unreconciled_domain)
            rec.unreconciled = len(unreconciled_items) > 0
            rec.amount_unreconciled = sum(unreconciled_items.mapped("amount_residual"))

    def _search_unreconciled(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise ValueError(_("Unsupported search operator"))
        acc_item = self.env["account.move.line"]
        domain = self._get_sale_unreconciled_base_domain()
        unreconciled_domain = expression.AND([domain, [("sale_order_id", "!=", False)]])
        unreconciled_items = acc_item.search(unreconciled_domain)
        unreconciled_sos = unreconciled_items.mapped("sale_order_id")
        if value:
            return [("id", "in", unreconciled_sos.ids)]
        else:
            return [("id", "not in", unreconciled_sos.ids)]

    def action_view_unreconciled(self):
        self.ensure_one()
        acc_item = self.env["account.move.line"]
        domain = self.with_company(
            self.company_id.id
        )._get_sale_unreconciled_base_domain()
        domain_account = self._get_account_domain()
        unreconciled_domain = expression.AND([domain, domain_account])
        unreconciled_domain = expression.AND(
            [unreconciled_domain, [("sale_order_id", "=", self.id)]]
        )
        unreconciled_domain.remove(("full_reconcile_id", "=", False))
        unreconciled_domain.remove("&")
        unreconciled_items = acc_item.search(unreconciled_domain)
        action = self.env.ref("account.action_account_moves_all")
        action_dict = action.read()[0]
        action_dict["domain"] = [("id", "in", unreconciled_items.ids)]
        return action_dict

    def action_reconcile(self):
        if (
            not self.company_id.sale_reconcile_account_id
            or not self.company_id.sale_reconcile_journal_id
        ):
            raise exceptions.ValidationError(
                _(
                    "The write-off account and jounral for sales is missing. An "
                    "accountant must fill that information"
                )
            )
        self.ensure_one()
        acc_item = self.env["account.move.line"]
        domain = self.with_company(
            self.company_id.id
        )._get_sale_unreconciled_base_domain()
        domain_account = self._get_account_domain()
        unreconciled_domain = expression.AND([domain, domain_account])
        unreconciled_domain = expression.AND(
            [unreconciled_domain, [("sale_order_id", "=", self.id)]]
        )
        unreconciled_items = acc_item.search(unreconciled_domain)
        writeoff_to_reconcile = self.env["account.move.line"]
        all_writeoffs = self.env["account.move.line"]
        reconciling_groups = self.env["account.move.line"].read_group(
            domain=unreconciled_domain,
            fields=["account_id", "product_id", "sale_line_id"],
            groupby=["account_id", "product_id", "sale_line_id"],
            lazy=False,
        )
        moves_to_reconcile = self.env["account.move.line"]
        products_considered = self.env["product.product"]
        main_product = self.env["product.product"]
        res = {}
        for group in reconciling_groups:
            account_id = group["account_id"][0]
            product_id = group["product_id"][0] if group["product_id"] else False
            sale_line_id = group["sale_line_id"][0] if group["sale_line_id"] else False
            if product_id and product_id in products_considered.ids:
                # avoid duplicate write-off for kits
                continue
            if sale_line_id and product_id:
                products, main_product = self.get_products(sale_line_id, product_id)
            else:
                products = self.env["product.product"]
            products_considered |= products
            unreconciled_items_group = unreconciled_items.filtered(
                lambda l: (
                    l.account_id.id == account_id and l.product_id.id in products.ids
                )
            )
            if float_is_zero(
                sum(unreconciled_items_group.mapped("amount_residual")),
                precision_rounding=self.company_id.currency_id.rounding,
            ):
                moves_to_reconcile = unreconciled_items_group
            else:
                if main_product:
                    # If kit, use the product of the kit
                    product_id = main_product.id
                writeoff_vals = self._get_sale_writeoff_vals(sale_line_id, product_id)
                if unreconciled_items_group:
                    writeoff_to_reconcile = (
                        unreconciled_items_group._create_so_writeoff(writeoff_vals)
                    )
                    all_writeoffs |= writeoff_to_reconcile
                    # add writeoff line to reconcile algorithm and finish the reconciliation
                    moves_to_reconcile = (
                        unreconciled_items_group | writeoff_to_reconcile
                    )
            # Check if reconciliation is total or needs an exchange rate entry to be
            # created
            if moves_to_reconcile:
                moves_to_reconcile.filtered(lambda l: not l.reconciled).reconcile()
            reconciled_ids = unreconciled_items | all_writeoffs
            res = {
                "name": _("Reconciled journal items"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "account.move.line",
                "domain": [("id", "in", reconciled_ids.ids)],
            }
        if self.env.context.get("bypass_unreconciled", False):
            # When calling the method from the wizard, lock after reconciling
            self.action_done()
        return res

    def get_products(self, sale_line_id, product_id):
        # if kit return the kit and components, otherwise just the product
        sale_line = self.env["sale.order.line"].browse(sale_line_id)
        boms = (
            sale_line.move_ids.filtered(lambda m: m.state != "cancel")
            .mapped("bom_line_id.bom_id")
            .filtered(lambda b: b.type == "phantom")
        )
        products = self.env["product.product"].browse(product_id)
        if boms:
            bom = boms[:1]
            boms, lines = bom.explode(sale_line.product_id, sale_line.product_uom_qty)
            for line, _line_data in lines:
                products |= line.product_id
            products |= sale_line.product_id
        return products, sale_line.product_id

    def _get_sale_writeoff_vals(self, sale_line_id, product_id):
        writeoff_date = self.env.context.get("writeoff_date", False)
        res = {
            "account_id": self.company_id.sale_reconcile_account_id.id,
            "journal_id": self.company_id.sale_reconcile_journal_id.id,
            "sale_order_id": self.id,
            "sale_line_id": sale_line_id or False,
            "product_id": product_id or False,
            "currency_id": self.currency_id.id or self.env.company.currency_id.id,
        }
        # hook for custom date:
        if writeoff_date:
            res.update({"date": writeoff_date})
        return res

    def reconcile_criteria(self):
        """Gets the criteria where SOs are locked or not, by default uses the company
        configuration"""
        self.ensure_one()
        return self.unreconciled and self.company_id.sale_lock_auto_reconcile

    def action_done(self):
        for rec in self:
            if rec.reconcile_criteria():
                exception_msg = rec.unreconciled_exception_msg()
                if exception_msg:
                    res = rec.sale_unreconciled_exception(exception_msg)
                    return res
                else:
                    rec.action_reconcile()
                    return super(SaleOrder, rec).action_done()
            else:
                return super(SaleOrder, rec).action_done()

    def action_cancel(self):
        for rec in self:
            if rec.reconcile_criteria():
                exception_msg = rec.unreconciled_exception_msg()
                if exception_msg:
                    res = rec.sale_unreconciled_exception(exception_msg)
                    return res
                else:
                    rec.action_reconcile()
                    return super(SaleOrder, rec).action_cancel()
            else:
                return super(SaleOrder, rec).action_cancel()

    def sale_unreconciled_exception(self, exception_msg=None):
        """This mean to be run when the SO cannot be reconciled because it is over
        tolerance"""
        self.ensure_one()
        if exception_msg:
            return (
                self.env["sale.unreconciled.exceeded.wiz"]
                .create(
                    {
                        "exception_msg": exception_msg,
                        "sale_id": self.id,
                        "origin_reference": "{},{}".format("sale.order", self.id),
                        "continue_method": "action_reconcile",
                    }
                )
                .action_show()
            )

    def unreconciled_exception_msg(self):
        self.ensure_one()
        exception_msg = ""
        amount_total = self.amount_total
        if self.currency_id and self.company_id.currency_id != self.currency_id:
            amount_total = self.currency_id._convert(
                amount_total,
                self.company_id.currency_id,
                self.company_id,
                fields.Date.today(),
            )
        if (
            self.company_id.sale_reconcile_tolerance
            and amount_total
            and abs(self.amount_unreconciled / amount_total)
            >= self.company_id.sale_reconcile_tolerance / 100.0
        ):
            params = {
                "amount_unreconciled": self.amount_unreconciled,
                "amount_allowed": self.amount_total
                * self.company_id.sale_reconcile_tolerance
                / 100.0,
            }
            exception_msg = (
                _(
                    "Finance Warning: \nUnreconciled amount is too high. Total "
                    "unreconciled amount: %(amount_unreconciled)s Maximum unreconciled"
                    " amount accepted: %(amount_allowed)s "
                )
                % params
            )
        return exception_msg
