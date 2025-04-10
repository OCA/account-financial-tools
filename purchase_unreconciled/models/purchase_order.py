# Copyright 2019-21 ForgeFlow S.L..
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.osv import expression
from odoo.tools import float_is_zero


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    unreconciled = fields.Boolean(
        compute="_compute_unreconciled",
        search="_search_unreconciled",
        help="Indicates that a Purchase Order has related Journal items not "
        "reconciled.\nNote that if it is false it can be either that "
        "everything is reconciled or that the related accounts do not "
        "allow reconciliation",
    )
    amount_unreconciled = fields.Float(compute="_compute_unreconciled")

    def _get_account_domain(self):
        included_accounts = (
            (
                self.env["product.category"]
                .with_company(self.company_id.id)
                .search([("property_valuation", "=", "real_time")])
            )
            .mapped("property_stock_account_input_categ_id")
            .ids
        )
        return [("account_id", "in", included_accounts)]

    @api.model
    def _get_purchase_unreconciled_base_domain(self):
        unreconciled_domain = [
            ("account_id.reconcile", "=", True),
            ("move_id.state", "=", "posted"),
            ("company_id", "in", self.env.companies.ids),
            # same condition than Odoo Unreconciled filter
            ("amount_residual", "!=", 0.0),
            ("balance", "!=", 0.0),
        ]
        return unreconciled_domain

    def _compute_unreconciled(self):
        acc_item = self.env["account.move.line"]
        for rec in self:
            domain = rec.with_company(
                rec.company_id
            )._get_purchase_unreconciled_base_domain()
            domain_account = rec._get_account_domain()
            unreconciled_domain = expression.AND([domain, domain_account])
            unreconciled_domain = expression.AND(
                [unreconciled_domain, [("purchase_order_id", "=", rec.id)]]
            )
            unreconciled_items = acc_item.search(unreconciled_domain)
            rec.unreconciled = len(unreconciled_items) > 0
            rec.amount_unreconciled = sum(unreconciled_items.mapped("amount_residual"))

    def _search_unreconciled(self, operator, value):
        if operator not in ("=", "!=") or not isinstance(value, bool):
            raise ValueError(_("Unsupported search operator"))
        acc_item = self.env["account.move.line"]
        domain = self._get_purchase_unreconciled_base_domain()
        domain = expression.AND([domain, [("purchase_order_id", "!=", False)]])
        domain_account = self._get_account_domain()
        domain = expression.AND([domain_account, domain])
        acc_items = acc_item.search(domain)
        unreconciled_pos_ids = acc_items.mapped("purchase_order_id").ids
        if value:
            return [("id", "in", unreconciled_pos_ids)]
        else:
            return [("id", "not in", unreconciled_pos_ids)]

    def action_view_unreconciled(self):
        self.ensure_one()
        acc_item = self.env["account.move.line"]
        domain = self.with_company(
            self.company_id.id
        )._get_purchase_unreconciled_base_domain()
        domain_account = self._get_account_domain()
        unreconciled_domain = expression.AND([domain, domain_account])
        unreconciled_domain = expression.AND(
            [unreconciled_domain, [("purchase_order_id", "=", self.id)]]
        )
        unreconciled_domain.remove(("amount_residual", "!=", 0.0))
        unreconciled_domain.remove("&")
        unreconciled_items = acc_item.search(unreconciled_domain)
        action = self.env.ref("account.action_account_moves_all")
        action_dict = action.read()[0]
        action_dict["domain"] = [("id", "in", unreconciled_items.ids)]
        return action_dict

    def action_reconcile(self):
        if (
            not self.company_id.purchase_reconcile_account_id
            or not self.company_id.purchase_reconcile_journal_id
        ):
            raise exceptions.ValidationError(
                _(
                    "The write-off account and journal for purchases is missing. An "
                    "accountant must fill that information"
                )
            )
        self.ensure_one()
        res = {}
        domain = self._get_purchase_unreconciled_base_domain()
        domain_account = self._get_account_domain()
        unreconciled_domain = expression.AND([domain, domain_account])
        unreconciled_domain = expression.AND(
            [domain, [("purchase_order_id", "=", self.id)]]
        )
        unreconciled_domain = expression.AND(
            [unreconciled_domain, [("company_id", "=", self.company_id.id)]]
        )
        writeoff_to_reconcile = self.env["account.move.line"]
        all_writeoffs = self.env["account.move.line"]
        reconciling_groups = self.env["account.move.line"].read_group(
            domain=unreconciled_domain,
            fields=["account_id", "product_id", "oca_purchase_line_id"],
            groupby=["account_id", "product_id", "oca_purchase_line_id"],
            lazy=False,
        )
        unreconciled_items = self.env["account.move.line"].search(unreconciled_domain)
        for group in reconciling_groups:
            account_id = group["account_id"][0]
            product_id = group["product_id"][0] if group["product_id"] else False
            purchase_line_id = (
                group["oca_purchase_line_id"][0]
                if group["oca_purchase_line_id"]
                else False
            )
            unreconciled_items_group = unreconciled_items.filtered(
                lambda line, account_id=account_id, product_id=product_id: (
                    line.account_id.id == account_id
                    and line.product_id.id == product_id
                )
            )
            # Check which type of force reconciling we are doing:
            # - Force reconciling amount_residual
            # - Force reconciling amount_residual_currency
            amount_residual_currency_reconcile = any(
                unreconciled_items_group.filtered(
                    lambda item_group,
                    account_id=account_id: item_group.amount_residual_currency != 0.0
                    and item_group.account_id.id == account_id
                )
            )
            if amount_residual_currency_reconcile:
                residual_field = "amount_residual_currency"
            else:
                residual_field = "amount_residual"
            if float_is_zero(
                sum(unreconciled_items_group.mapped(residual_field)),
                precision_rounding=self.company_id.currency_id.rounding,
            ):
                moves_to_reconcile = unreconciled_items_group
            else:
                writeoff_vals = self._get_purchase_writeoff_vals(
                    unreconciled_items_group, purchase_line_id, product_id
                )
                writeoff_to_reconcile = unreconciled_items_group._create_writeoff(
                    writeoff_vals
                )
                all_writeoffs |= writeoff_to_reconcile
                # add writeoff line to reconcile algorithm and finish the reconciliation
                moves_to_reconcile = unreconciled_items_group | writeoff_to_reconcile
            # Check if reconciliation is total or needs an exchange rate entry to be
            # created
            if moves_to_reconcile:
                moves_to_reconcile.filtered(
                    lambda move: not move.reconciled
                ).reconcile()
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
            self.button_done()
        return res

    def _get_purchase_writeoff_vals(self, amls, purchase_line_id, product_id):
        writeoff_date = self.env.context.get("writeoff_date", False)
        aml_date = max(amls.mapped("move_id.date"))
        res = {
            "account_id": self.company_id.purchase_reconcile_account_id.id,
            "journal_id": self.company_id.purchase_reconcile_journal_id.id,
            "purchase_order_id": self.id,
            "purchase_line_id": purchase_line_id or False,
            "product_id": product_id,
            "currency_id": self.currency_id.id or self.env.company.currency_id.id,
            "date": aml_date,
        }
        # hook for custom date:
        if writeoff_date:
            res.update({"date": writeoff_date})
        return res

    def reconcile_criteria(self):
        """Gets the criteria where POs are locked or not, by default uses the company
        configuration"""
        self.ensure_one()
        return self.unreconciled and self.company_id.purchase_lock_auto_reconcile

    def button_done(self):
        for rec in self:
            criteria = rec.reconcile_criteria()
            if criteria:
                if rec.unreconciled:
                    exception_msg = rec.unreconciled_exception_msg()
                    if exception_msg:
                        res = rec.purchase_unreconciled_exception(exception_msg)
                        return res
                    else:
                        rec.action_reconcile()
                        return super(PurchaseOrder, rec).button_done()
                else:
                    return super(PurchaseOrder, rec).button_done()
            else:
                return super(PurchaseOrder, rec).button_done()

    def purchase_unreconciled_exception(self, exception_msg=None):
        """This mean to be run when the SO cannot be reconciled because it is over
        tolerance"""
        self.ensure_one()
        if exception_msg:
            return (
                self.env["purchase.unreconciled.exceeded.wiz"]
                .create(
                    {
                        "exception_msg": exception_msg,
                        "purchase_id": self.id,
                        "origin_reference": "{},{}".format("purchase.order", self.id),
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
            self.company_id.purchase_reconcile_tolerance
            and amount_total
            and abs(self.amount_unreconciled / amount_total)
            >= self.company_id.purchase_reconcile_tolerance / 100.0
        ):
            params = {
                "amount_unreconciled": self.amount_unreconciled,
                "amount_allowed": self.amount_total
                * self.company_id.purchase_reconcile_tolerance
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
