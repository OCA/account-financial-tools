# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restrict_mode_hash_table = fields.Boolean(
        default=lambda self: self._default_restrict_mode_hash_table(), readonly=True
    )

    @api.constrains("restrict_mode_hash_table")
    def _check_journal_restrict_mode(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_account_journal_restrict_mode")
        )
        if not test_condition:
            return
        for rec in self:
            if not rec.restrict_mode_hash_table:
                raise UserError(
                    self.env._("Journal %s must have Lock Posted Entries enabled.")
                    % rec.name
                )

    def _default_restrict_mode_hash_table(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_account_journal_restrict_mode")
        )
        return bool(test_condition)
