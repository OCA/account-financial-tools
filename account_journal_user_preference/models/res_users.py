# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    use_preferred_journals = fields.Boolean(
        string="Prioritize Preferred Journals",
        default=True,
        help="Prioritize configured journals when searching for a journal.",
    )
    preferred_journal_ids = fields.One2many(
        "account.journal.user.preferred",
        "user_id",
        string="Preferred Journals",
        copy=False,
    )

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            "use_preferred_journals",
            "preferred_journal_ids",
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            "use_preferred_journals",
            "preferred_journal_ids",
        ]
