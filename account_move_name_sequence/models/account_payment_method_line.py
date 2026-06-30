# Copyright 2026 Ecosoft (http://ecosoft.co.th/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountPaymentMethodLine(models.Model):
    _inherit = "account.payment.method.line"

    sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Entry Sequence",
        copy=False,
        check_company=True,
        help="This sequence will be used to generate the journal entry number.",
    )
