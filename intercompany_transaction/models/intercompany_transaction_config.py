# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class IntercompanyTransactionConfig(models.Model):
    _name = "intercompany.transaction.config"
    _description = "Intercompany Transaction Config"
    _rec_name = "from_company_id"

    from_company_id = fields.Many2one(
        "res.company",
        ondelete="cascade",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    from_company_debit_account_id = fields.Many2one(
        "account.account",
        "Debit Account(From Company)",
        index=True,
    )
    to_company_id = fields.Many2one(
        "res.company",
        ondelete="cascade",
        required=True,
        index=True,
    )
    to_company_debit_account_id = fields.Many2one(
        "account.account",
        "Debit Account(To Company)",
        index=True,
    )
    to_company_credit_account_id = fields.Many2one(
        "account.account",
        "Credit Account(To Company)",
        index=True,
    )
    to_company_journal_id = fields.Many2one(
        "account.journal",
        string="Journal",
        index=True,
    )
    active = fields.Boolean(default=True, index=True)

    _sql_constraints = [
        (
            "unique_from_to_company",
            "UNIQUE(from_company_id, to_company_id)",
            "Intercompany Transaction Configuration already exists "
            "for this company pair!",
        ),
    ]

    @api.constrains("from_company_id", "to_company_id")
    def _check_record_validity(self) -> None:
        """Validate company configuration."""
        for rec in self:
            if rec.from_company_id and rec.to_company_id:
                # Prevent circular configuration (same company)
                if rec.from_company_id == rec.to_company_id:
                    raise ValidationError(
                        self.env._(
                            "Cannot create intercompany configuration "
                            "with the same company: %(company)s",
                            company=rec.from_company_id.name,
                        )
                    )
