# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    fiscalyear_lock_date = fields.Date(
        string="Lock Date",
        help="No users, including Advisers, can edit accounts prior "
        "to and inclusive of this date for this journal. Use it "
        "for fiscal year locking for this journal, for example.",
    )
    period_lock_date = fields.Date(
        string="Lock Date for Non-Advisers",
        help="Only users with the 'Adviser' role can edit accounts "
        "prior to and inclusive of this date for this journal. "
        "Use it for period locking inside an open fiscal year "
        "for this journal, for example.",
    )
