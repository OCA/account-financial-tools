# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restrict_mode_hash_table = fields.Boolean(default=True, readonly=True)

    @api.constrains("restrict_mode_hash_table")
    def _check_journal_restrict_mode(self):
        for rec in self:
            if not rec.restrict_mode_hash_table:
                raise UserError(
                    _("Journal %s must have Lock Posted Entries enabled.") % rec.name
                )

    @api.model_create_multi
    def create(self, vals_list):
        # Proposed fix to odoo https://github.com/odoo/odoo/pull/147738.
        # But while they don't merge (as it's not an issue they will face in Odoo standard...)
        journals = super().create(vals_list)
        for journal in journals:
            if journal.restrict_mode_hash_table and not journal.secure_sequence_id:
                journal._create_secure_sequence(["secure_sequence_id"])
        return journals
