# Copyright 2021 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    unreconciled = fields.Boolean(
        compute="_compute_unreconciled",
        search="_search_unreconciled",
        help="""Indicates that a sale Order has related Journal items not
             reconciled.Note that if it is false it can be either that
             everything is reconciled or that the related accounts do not
             allow reconciliation""",
    )
    amount_unreconciled = fields.Float(compute="_compute_unreconciled")

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
            # for some reason when amount_residual is zero
            # is marked as reconciled, this is better check
            ("full_reconcile_id", "=", False),
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
        if operator != "=" or not isinstance(value, bool):
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
        domain = self._get_sale_unreconciled_base_domain()
        domain_account = self._get_account_domain()
        unreconciled_domain = expression.AND([domain, domain_account])
        unreconciled_domain = expression.AND(
            [unreconciled_domain, [("sale_order_id", "=", self.id)]]
        )
        unreconciled_items = acc_item.search(unreconciled_domain)
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
                # nothing to reconcile
                # if journal items are zero zero then we force a matching number
                if all(
                    not x.amount_residual and not x.amount_residual_currency
                    for x in unreconciled_items_currency
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
                    "account_id": self.company_id.sale_reconcile_account_id.id,
                    "journal_id": self.company_id.sale_reconcile_journal_id.id,
                    "sale_order_id": self.id,
                    "currency_id": currency.id,
                }
                if not all_aml_share_same_currency:
                    writeoff_vals["amount_currency"] = False
                writeoff_to_reconcile |= (
                    unreconciled_items_currency._create_so_writeoff(writeoff_vals)
                )
                all_writeoffs |= writeoff_to_reconcile
                # add writeoff line to reconcile algorithm and finish the reconciliation
                remaining_moves = unreconciled_items_currency | writeoff_to_reconcile
                # Check if reconciliation is total or needs an exchange rate entry to be created
                if remaining_moves:
                    remaining_moves.filtered(
                        lambda l: l.balance != 0.0
                    ).remove_move_reconcile()
                    remaining_moves.filtered(lambda l: l.balance != 0.0).reconcile()
                    # There are some journal items that are zero balance that shows
                    # as unreconciled, we just attached the full reconcile just created
                    full_reconcile_id = remaining_moves.mapped("full_reconcile_id")
                    full_reconcile_id = full_reconcile_id and full_reconcile_id[0]
                    remaining_moves.filtered(
                        lambda l: l.balance == 0.0 and not l.full_reconcile_id
                    ).write({"full_reconcile_id": full_reconcile_id})
            reconciled_ids = unreconciled_items | all_writeoffs
            return {
                "name": _("Reconciled journal items"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "account.move.line",
                "domain": [("id", "in", reconciled_ids.ids)],
            }

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
