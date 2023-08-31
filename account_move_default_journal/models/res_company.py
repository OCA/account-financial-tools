# Copyright 2023 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    default_general_journal_id = fields.Many2one(
        "account.journal", string="Default journal for new general bookings"
    )
    default_sale_journal_id = fields.Many2one(
        "account.journal", string="Default journal for new sale bookings"
    )
    default_purchase_journal_id = fields.Many2one(
        "account.journal", string="Default journal for new purchase bookings"
    )
