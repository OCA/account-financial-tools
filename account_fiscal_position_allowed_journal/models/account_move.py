# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_fiscal_position_journal_domain(self):
        self.ensure_one()
        return Domain(
            "id", "in", self.fiscal_position_id.sudo().allowed_journal_ids.ids
        )

    @api.depends("fiscal_position_id")
    def _compute_suitable_journal_ids(self):
        res = super()._compute_suitable_journal_ids()
        for rec in self:
            if not rec.fiscal_position_id:
                continue
            journal_domain = rec._get_fiscal_position_journal_domain()
            rec.suitable_journal_ids = rec.suitable_journal_ids.filtered_domain(
                journal_domain
            )
        return res

    @api.depends("fiscal_position_id")
    def _compute_journal_id(self):
        res = super()._compute_journal_id()
        for rec in self:
            if not rec.fiscal_position_id.sudo().allowed_journal_ids:
                continue
            rec.journal_id = rec._search_default_journal()
        return res

    def _search_default_journal(self):
        res = super()._search_default_journal()
        if self.fiscal_position_id:
            journal_type = self._get_valid_journal_types()[0]
            allowed_journal = self.fiscal_position_id._get_allowed_journal(journal_type)
            res = allowed_journal or res
        return res

    def _check_journal_allowed_fiscal_position(self):
        """
        This method checks whether the journal of the invoice is allowed for the
        selected fiscal position.
        If no fiscal position or no allowed journal on the fiscal position, always OK.
        :raise: UserError if not allowed
        """
        for rec in self:
            if (
                rec.is_invoice(include_receipts=True)
                and rec.fiscal_position_id
                and rec.fiscal_position_id.sudo().allowed_journal_ids
                and rec.journal_id not in rec.suitable_journal_ids
            ):
                raise UserError(
                    self.env._(
                        "Journal %(journal_name)s is not allowed for fiscal "
                        "position %(fp_name)s.",
                        journal_name=rec.journal_id.display_name,
                        fp_name=rec.fiscal_position_id.display_name,
                    )
                )

    def action_post(self):
        self._check_journal_allowed_fiscal_position()
        return super().action_post()
