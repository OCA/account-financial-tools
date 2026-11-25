# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.constrains("active", "company_id")
    def _check_partner_company_consistency(self):
        partners = self.filtered(lambda p: p.active and p.company_id)
        if not partners:
            return

        partner_company_ids = self._get_partner_company_ids_from_moves(partners)
        for partner in partners:
            company_ids = partner_company_ids.get(partner.id, set())
            if not company_ids:
                continue
            # Partner is already used across multiple companies or in a different
            # company than the one being assigned.
            if partner.company_id.id not in company_ids or len(company_ids) > 1:
                raise ValidationError(
                    self.env._(
                        "You can't update the company because there are journal "
                        "entries for this partner in a different company."
                    )
                )

    def _get_partner_company_ids_from_moves(self, partners):
        """Return a map {partner_id: set(company_ids)} from moves and move lines."""
        partner_company_ids = {}
        for model in ("account.move.line", "account.move"):
            for partner, company_id in (
                self.env[model]
                .sudo()
                ._read_group(
                    domain=[("partner_id", "in", partners.ids)],
                    groupby=["partner_id", "company_id"],
                )
            ):
                if not company_id:
                    continue
                partner_company_ids.setdefault(partner.id, set()).add(company_id.id)
        return partner_company_ids
