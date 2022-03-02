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

    @api.model
    def _get_sale_unreconciled_base_domain(self):
        included_accounts = (
            (
                self.env["product.category"].search(
                    [("property_valuation", "=", "real_time")]
                )
            )
            .mapped("property_stock_account_output_categ_id")
            .ids
        )
        unreconciled_domain = [
            ("account_id.reconcile", "=", True),
            ("account_id", "in", included_accounts),
            ("move_id.state", "=", "posted"),
            # for some reason when amount_residual is zero
            # is marked as reconciled, this is better check
            ("full_reconcile_id", "=", False),
            ("company_id", "in", self.env.companies.ids),
        ]
        return unreconciled_domain

    def _compute_unreconciled(self):
        acc_item = self.env["account.move.line"]
        for rec in self:
            domain = rec._get_sale_unreconciled_base_domain()
            unreconciled_domain = expression.AND(
                [domain, [("sale_order_id", "=", rec.id)]]
            )
            unreconciled_items = acc_item.search(unreconciled_domain)
            rec.unreconciled = len(unreconciled_items) > 0

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
        domain = self._get_sale_unreconciled_base_domain()
        unreconciled_domain = expression.AND(
            [domain, [("sale_order_id", "=", self.id)]]
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
        unreconciled_domain = expression.AND(
            [domain, [("sale_order_id", "=", self.id)]]
        )
        unreconciled_items = acc_item.search(unreconciled_domain)
        writeoff_to_reconcile = False
        for account in unreconciled_items.mapped("account_id"):
            acc_unrec_items = unreconciled_items.filtered(
                lambda ml: ml.account_id == account
            )
            # First try to reconcile the lines automatically to prevent unwanted
            # write-offs
            if not sum(acc_unrec_items.mapped("amount_residual")) and not sum(
                acc_unrec_items.mapped("amount_residual_currency")
            ):
                # nothing to reconcile
                continue
            all_aml_share_same_currency = all(
                [x.currency_id == self[0].currency_id for x in acc_unrec_items]
            )
            writeoff_vals = {
                "account_id": self.company_id.sale_reconcile_account_id.id,
                "journal_id": self.company_id.sale_reconcile_journal_id.id,
                "sale_order_id": self.id,
                "currency_id": self.currency_id.id,
            }
            if not all_aml_share_same_currency:
                writeoff_vals["amount_currency"] = False
            if writeoff_to_reconcile:
                writeoff_to_reconcile += unreconciled_items._create_so_writeoff(
                    writeoff_vals
                )
            else:
                writeoff_to_reconcile = unreconciled_items._create_so_writeoff(
                    writeoff_vals
                )
        # add writeoff line to reconcile algorithm and finish the reconciliation
        if writeoff_to_reconcile:
            remaining_moves = unreconciled_items + writeoff_to_reconcile
        else:
            remaining_moves = unreconciled_items
        # Check if reconciliation is total or needs an exchange rate entry to be created
        if remaining_moves:
            remaining_moves.filtered(lambda l: not l.reconciled).reconcile()
            if writeoff_to_reconcile:
                reconciled_ids = unreconciled_items + writeoff_to_reconcile
            else:
                reconciled_ids = unreconciled_items
            return {
                "name": _("Reconciled journal items"),
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "account.move.line",
                "domain": [("id", "in", reconciled_ids.ids)],
            }

    def action_done(self):
        for rec in self:
            if rec.unreconciled:
                rec.action_reconcile()
        return super(SaleOrder, self).action_done()
