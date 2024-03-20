# Copyright 2021-2023 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    account_move_default_general_journal_id = fields.Many2one(
        "account.journal",
        string="Default journal for new miscellaneous bookings",
        related="company_id.default_general_journal_id",
    )
    account_move_default_sale_journal_id = fields.Many2one(
        "account.journal",
        string="Default journal for new sale bookings",
        related="company_id.default_sale_journal_id",
    )
    account_move_default_purchase_journal_id = fields.Many2one(
        "account.journal",
        string="Default journal for new purchase bookings",
        related="company_id.default_purchase_journal_id",
    )
