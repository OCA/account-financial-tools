# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    allowed_journal_ids = fields.Many2many(
        string="Allowed journals", comodel_name="account.journal"
    )

    def _get_allowed_journal(self, journal_type):
        """
        Returns the journal matching the given type only if there is only one.
        :return: account.journal record
        """
        self.ensure_one()
        journals = self.allowed_journal_ids.filtered(lambda j: j.type == journal_type)
        return journals if len(journals) == 1 else self.env["account.journal"].browse()
