from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    analytic_accounts = fields.Char(
        compute="_compute_analytic_accounts",
        store=True,
    )

    @api.depends("analytic_line_ids")
    def _compute_analytic_accounts(self):
        for record in self:
            record.analytic_accounts = ", ".join(
                [
                    getattr(analytic_line, field).display_name
                    for analytic_line in record.analytic_line_ids
                    for field in [
                        field_name
                        for field_name in record.analytic_line_ids._fields.keys()
                        if field_name.startswith("x_plan")
                    ]
                    + ["account_id"]
                    if getattr(record.analytic_line_ids, field, False)
                ]
            )
