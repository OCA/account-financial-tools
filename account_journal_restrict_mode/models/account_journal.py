# Copyright 2023 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools import config


class AccountJournal(models.Model):
    _inherit = "account.journal"

    restrict_mode_hash_table = fields.Boolean(
        compute="_compute_restrict_mode_hash_table", store=True, readonly=True
    )

    @api.constrains("restrict_mode_hash_table", "type")
    def _check_journal_restrict_mode(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_account_journal_restrict_mode")
        )
        if not test_condition:
            return
        for rec in self:
            if not rec.restrict_mode_hash_table and rec.type in [
                "sale",
                "purchase",
                "general",
            ]:
                raise UserError(
                    self.env._("Journal %s must have Lock Posted Entries enabled.")
                    % rec.name
                )

    @api.depends("type")
    def _compute_restrict_mode_hash_table(self):
        test_condition = not config["test_enable"] or (
            config["test_enable"]
            and self.env.context.get("test_account_journal_restrict_mode")
        )
        for rec in self:
            if not test_condition:
                rec.restrict_mode_hash_table = False
                continue
            rec.restrict_mode_hash_table = rec.type in ["sale", "purchase", "general"]
