# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountJournalUserPreferred(models.Model):
    _name = "account.journal.user.preferred"
    _description = "User Preferred Journal"
    _rec_name = "journal_id"
    _order = "sequence, id"

    journal_id = fields.Many2one("account.journal", required=True, ondelete="cascade")
    user_id = fields.Many2one(
        "res.users",
        required=True,
        default=lambda self: self.env.user,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)

    _sql_constraints = [
        (
            "user_journal_unique",
            "unique(user_id, journal_id)",
            "A journal can only appear once in a user's preferences.",
        ),
    ]
