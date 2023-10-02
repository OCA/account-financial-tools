# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restrict_mode_hash_table = fields.Boolean(default=True)

    @api.constrains("restrict_mode_hash_table")
    def _check_journal_restrict_mode(self):
        for rec in self:
            if not rec.restrict_mode_hash_table:
                raise UserError(
                    _("Journal %s must have Lock Posted Entries enabled.") % rec.name
                )
