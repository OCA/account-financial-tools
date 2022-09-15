# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError
from odoo.addons.account.models.account_invoice import TYPE2JOURNAL


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.onchange("fiscal_position_id")
    def _onchange_fiscal_position_allowed_journal(self):
        self.ensure_one()
        journal_type = TYPE2JOURNAL[self.type]
        journal_domain = [
            ("company_id", "=", self.company_id.id),
            ("type", "=", journal_type),
        ]
        if self.fiscal_position_id:
            allowed_journal = self.fiscal_position_id._get_allowed_journal(journal_type)
            if allowed_journal:
                self.journal_id = allowed_journal
            journal_domain.append(
                ("id", "in", self.fiscal_position_id.allowed_journal_ids.ids)
            )
        return {"domain": {"journal_id": journal_domain}}

    @api.model
    def create(self, vals):
        invoice = super(AccountInvoice, self).create(vals)
        invoice._onchange_fiscal_position_allowed_journal()
        invoice._convert_to_write(invoice._cache)
        return invoice

    def _check_journal_allowed_fiscal_position(self):
        """
        This method checks whether the journal of the invoice is allowed for the
        selected fiscal position.
        If no fiscal position or no allowed journal on the fiscal position, always OK.
        :raise: UserError if not allowed
        """
        for rec in self:
            if (
                rec.fiscal_position_id
                and rec.fiscal_position_id.allowed_journal_ids
                and rec.journal_id not in rec.fiscal_position_id.allowed_journal_ids
            ):
                raise UserError(
                    _(
                        "Journal {journal_name} is not allowed for fiscal position "
                        "{fp_name}."
                    ).format(
                        journal_name=rec.journal_id.display_name,
                        fp_name=rec.fiscal_position_id.display_name,
                    )
                )

    def invoice_validate(self):
        self._check_journal_allowed_fiscal_position()
        return super().invoice_validate()
