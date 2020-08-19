# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Contract(models.Model):
    _inherit = "contract.contract"

    def _recurring_create_invoice(self, date_ref=False):
        invoices = super()._recurring_create_invoice(date_ref)
        for invoice_line in invoices.mapped("line_ids"):
            spread_template = invoice_line.contract_line_id.spread_template_id
            if spread_template:
                account = invoice_line.account_id
                spread_account_id = False
                if spread_template.use_invoice_line_account:
                    account = spread_template.exp_rev_account_id
                    spread_account_id = invoice_line.account_id.id

                spread_vals = spread_template._prepare_spread_from_template(
                    spread_account_id=spread_account_id
                )
                date_invoice = invoice_line.move_id.invoice_date
                date_invoice = date_invoice or spread_template.start_date
                date_invoice = date_invoice or fields.Date.today()
                spread_vals["spread_date"] = date_invoice

                spread_vals["name"] = ("%s %s") % (
                    spread_vals["name"],
                    invoice_line.name,
                )

                if spread_vals["invoice_type"] == "out_invoice":
                    spread_vals["credit_account_id"] = account.id
                else:
                    spread_vals["debit_account_id"] = account.id

                analytic_account = invoice_line.analytic_account_id
                spread_vals["account_analytic_id"] = analytic_account.id

                spread = self.env["account.spread"].create(spread_vals)

                analytic_tags = invoice_line.analytic_tag_ids
                spread.analytic_tag_ids = analytic_tags

                invoice_line.spread_id = spread
        return invoices
