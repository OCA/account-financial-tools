# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    loan_line_id = fields.Many2one(
        "account.loan.line",
        readonly=True,
        ondelete="restrict",
    )
    loan_id = fields.Many2one(
        "account.loan",
        readonly=True,
        store=True,
        ondelete="restrict",
    )

    def _post(self, *args, **kwargs):
        res = super()._post(*args, **kwargs)
        for record in self:
            if loan_line_id := record.loan_line_id:
                record.loan_id = loan_line_id.loan_id
                if record.state == "posted":
                    record.loan_line_id._check_move_amount()
                    if record.loan_line_id.sequence == record.loan_id.periods:
                        record.loan_id.close()
        return res
