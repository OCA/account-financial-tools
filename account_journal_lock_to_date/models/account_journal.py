# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    fiscalyear_lock_to_date = fields.Date(
        string="Lock To Date",
        help="No users, including Advisers, can edit accounts posterior "
        "to and inclusive of this date for this journal.",
    )
    period_lock_to_date = fields.Date(
        string="Lock To Date for Non-Advisers",
        help="Only users with the 'Adviser' role can edit accounts "
        "posterior to and inclusive of this date for this journal.",
    )
