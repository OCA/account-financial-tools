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

    def action_post(self):
        res = super().action_post()
        for record in self:
            loan_line_id = record.loan_line_id
            if loan_line_id:
                record.loan_id = loan_line_id.loan_id
                record.loan_line_id._check_move_amount()
                record.loan_line_id.loan_id._compute_posted_lines()
                if record.loan_line_id.sequence == record.loan_id.periods:
                    record.loan_id.close()
        return res
