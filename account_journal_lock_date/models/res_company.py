# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_user_fiscal_lock_date(self, journal, ignore_exceptions=False):
        lock_date = super()._get_user_fiscal_lock_date(
            journal, ignore_exceptions=ignore_exceptions
        )
        if journal and journal.exists():
            return max(lock_date or date.min, journal.user_journal_lock_date)
        return lock_date
