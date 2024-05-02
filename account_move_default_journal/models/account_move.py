# Copyright 2021-2023 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _search_default_journal(self, journal_types):
        company_id = self._context.get("default_company_id", self.env.company.id)
        company = self.env["res.company"].browse(company_id)

        # Use the appropriate config parameter for the journal type
        journal = None
        if "sale" in journal_types:
            journal = company.default_sale_journal_id
        elif "purchase" in journal_types:
            journal = company.default_purchase_journal_id
        elif "general" in journal_types:
            journal = company.default_general_journal_id

        # Use the found journal, otherwise default back to normal behavior
        if journal:
            default_currency_id = self._context.get("default_currency_id")
            if (
                not default_currency_id
                or journal.currency_id.id == default_currency_id.id
            ):
                return journal
        return super()._search_default_journal(journal_types)
