# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.osv import expression


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

    @api.model
    def _get_purchase_unreconciled_base_domain(self):
        included_accounts = (
            (
                self.env["product.category"].search(
                    [("property_valuation", "=", "real_time")]
                )
            )
            .mapped("property_stock_account_input_categ_id")
            .ids
        )
        unreconciled_domain = [
            ("account_id.reconcile", "=", True),
            ("account_id", "in", included_accounts),
            ("move_id.state", "=", "posted"),
            ("company_id", "in", self.env.companies.ids),
            # for some reason when amount_residual is zero
            # is marked as reconciled, this is better check
            ("amount_residual", "!=", 0.0),
        ]
        return unreconciled_domain

    def _compute_unreconciled(self):
        acc_item = self.env["account.move.line"]
        for rec in self:
            domain = rec.with_company(
                rec.company_id
            )._get_purchase_unreconciled_base_domain()
            unreconciled_domain = expression.AND(
                [domain, [("purchase_order_id", "=", rec.id)]]
            )
            unreconciled_items = acc_item.search(unreconciled_domain)
            rec.unreconciled = len(unreconciled_items) > 0
            rec.amount_unreconciled = sum(unreconciled_items.mapped("amount_residual"))

    def _search_unreconciled(self, operator, value):
        if operator != "=" or not isinstance(value, bool):
            raise ValueError(_("Unsupported search operator"))
        acc_item = self.env["account.move.line"]
        domain = self._get_purchase_unreconciled_base_domain()
        unreconciled_domain = expression.AND(
            [domain, [("purchase_order_id", "!=", False)]]
        )
        unreconciled_items = acc_item.search(unreconciled_domain)
        unreconciled_pos = unreconciled_items.mapped("purchase_order_id")
        if value:
            return [("id", "in", unreconciled_pos.ids)]
        else:
            return [("id", "not in", unreconciled_pos.ids)]

    def action_view_unreconciled(self):
        self.ensure_one()
        acc_item = self.env["account.move.line"]
        domain = self.with_company(
            self.company_id.id
        )._get_purchase_unreconciled_base_domain()
        unreconciled_domain = expression.AND([domain, [("purchase_id", "=", self.id)]])
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
                    "The write-off account and jounral for purchases is missing. An "
                    "accountant must fill that information"
                )
            )
        self.ensure_one()
        res = {}
        domain = self._get_purchase_unreconciled_base_domain()
        unreconciled_domain = expression.AND(
            [domain, [("purchase_order_id", "=", self.id)]]
        )
        unreconciled_domain = expression.AND(
            [unreconciled_domain, [("company_id", "=", self.company_id.id)]]
        )
        unreconciled_items = self.env["account.move.line"].search(unreconciled_domain)
        writeoff_to_reconcile = self.env["account.move.line"]
        all_writeoffs = self.env["account.move.line"]
        for account in unreconciled_items.mapped("account_id"):
            acc_unrec_items = unreconciled_items.filtered(
                lambda ml: ml.account_id == account
            )
            for currency in acc_unrec_items.mapped("currency_id"):
                unreconciled_items_currency = acc_unrec_items.filtered(
                    lambda l: l.currency_id == currency
                )
                remaining_moves = self.env["account.move.line"]
                # nothing to reconcile
                # if journal items are zero zero then we force a matching number
                if all(
                    not x.amount_residual and not x.amount_residual_currency
                    for x in unreconciled_items_currency
                ):
                    if (
                        sum(unreconciled_items.mapped("balance")) == 0
                        and sum(unreconciled_items.mapped("debit")) == 0
                    ):
                        self.env["account.full.reconcile"].create(
                            {
                                "reconciled_line_ids": [(6, 0, unreconciled_items.ids)],
                            }
                        )
                        continue
                all_aml_share_same_currency = all(
                    [
                        x.currency_id == self[0].currency_id
                        for x in unreconciled_items_currency
                    ]
                )
                writeoff_vals = {
                    "account_id": self.company_id.purchase_reconcile_account_id.id,
                    "journal_id": self.company_id.purchase_reconcile_journal_id.id,
                    "purchase_order_id": self.id,
                    "currency_id": currency.id,
                }
                if not all_aml_share_same_currency:
                    writeoff_vals["amount_currency"] = False
                writeoff_to_reconcile |= unreconciled_items_currency._create_writeoff(
                    writeoff_vals
                )
                all_writeoffs |= writeoff_to_reconcile
                # add writeoff line to reconcile algorithm and finish the reconciliation
                remaining_moves = unreconciled_items_currency | writeoff_to_reconcile
                # Check if reconciliation is total or needs an exchange rate entry to be created
                if remaining_moves:
                    remaining_moves.filtered(
                        lambda l: l.amount_residual != 0.0
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

    def reconcile_criteria(self):
        """Gets the criteria where POs are locked or not, by default uses the company
        configuration"""
        self.ensure_one()
        return self.unreconciled and self.company_id.purchase_lock_auto_reconcile

    def button_done(self):
        for rec in self:
            if rec.unreconciled:
                exception_msg = rec.unreconciled_exception_msg()
                if exception_msg:
                    res = rec.purchase_unreconciled_exception(exception_msg)
                    return res
                else:
                    if rec.reconcile_criteria():
                        rec.action_reconcile()
                    return super(PurchaseOrder, self).button_done()
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
        if (
            self.company_id.purchase_reconcile_tolerance
            and self.amount_total
            and abs(self.amount_unreconciled / self.amount_total)
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
