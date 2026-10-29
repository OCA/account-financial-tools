# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _search(self, domain, offset=0, limit=None, order=None):
        """Prioritize the user's eligible journals before applying pagination."""
        # Odoo 18's search_fetch supplies _order for searches and dropdowns.
        if (
            order in (None, self._order)
            and self.env.user.use_preferred_journals
            and self.env.user.preferred_journal_ids
        ):
            query = super()._search(domain, limit=False, order=self._order)
            journals = self.browse(query)
            preferred_journals = (
                self.env.user.preferred_journal_ids.journal_id.filtered_domain(domain)
                & journals
            )
            other_journals = journals - preferred_journals
            journals = preferred_journals | other_journals
            stop = offset + limit if limit else None
            # Odoo 18 expects a Query, rather than a recordset, from _search.
            return journals[offset:stop]._as_query()
        return super()._search(domain, offset=offset, limit=limit, order=order)
