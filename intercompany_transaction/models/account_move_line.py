# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    transfer_to_company_id = fields.Many2one(
        "res.company", string="Transfer to", index=True
    )

    def _check_intercompany_transaction_config_missing_fields(
        self, intercompany_transaction_config_rec: models.Model
    ) -> None:
        """Validate required fields in intercompany config."""
        fields_to_check = [
            "from_company_debit_account_id",
            "to_company_debit_account_id",
            "to_company_credit_account_id",
            "to_company_journal_id",
        ]

        # Use list comprehension for better performance
        missing_fields_list = [
            intercompany_transaction_config_rec._fields[field].string
            for field in fields_to_check
            if not getattr(intercompany_transaction_config_rec, field)
        ]

        if missing_fields_list:
            raise ValidationError(
                self.env._(
                    "Missing following field(s) in Intercompany Transaction "
                    "Configuration('%(from_company)s -> %(to_company)s'):\n"
                    "%(missing_fields)s",
                    missing_fields="\n".join(missing_fields_list),
                    from_company=self.move_id.company_id.name,
                    to_company=self.transfer_to_company_id.name,
                )
            )

    def _get_move_line_intercompany_transaction_config(
        self, config_cache: dict[tuple[int, int], models.Model] | None = None
    ) -> models.Model:
        """Get and validate intercompany transaction configuration.

        :param config_cache: Optional dict mapping (from_co_id, to_co_id) -> record
        """
        self.ensure_one()

        # Early validation
        if self.move_id.move_type != "entry":
            raise ValidationError(self.env._("'Type' must be 'Journal Entry'!"))

        if not self.move_id.is_intercompany_journal_entry:
            raise ValidationError(
                self.env._(
                    "The 'Transfer To' field can only be set for Intercompany "
                    "Transaction journal entries created from the "
                    "Intercompany Transaction menu."
                )
            )

        if not self.transfer_to_company_id:
            raise ValidationError(self.env._("'Transfer to' is required!"))

        from_company_id = self.move_id.company_id.id
        to_company_id = self.transfer_to_company_id.id
        cache_key = (from_company_id, to_company_id)

        # Use cache if available
        if config_cache is not None and cache_key in config_cache:
            intercompany_transaction_config_rec = config_cache[cache_key]
        else:
            # Single search for config record
            intercompany_transaction_config_rec = self.env[
                "intercompany.transaction.config"
            ].search(
                [
                    ("from_company_id", "=", from_company_id),
                    ("to_company_id", "=", to_company_id),
                ],
                limit=1,
            )

        if not intercompany_transaction_config_rec:
            raise ValidationError(
                self.env._(
                    "Intercompany Transaction Configuration Not Found: "
                    "%(from_company)s -> %(to_company)s",
                    from_company=self.move_id.company_id.name,
                    to_company=self.transfer_to_company_id.name,
                )
            )

        if self.account_id:
            is_correct_account = (
                intercompany_transaction_config_rec.from_company_debit_account_id
                == self.account_id
            )

            if not is_correct_account:
                to_company_ids = self.move_id.line_ids.mapped(
                    "transfer_to_company_id"
                ).ids

                intercompany_trans_account_config_recs = self.env[
                    "intercompany.transaction.config"
                ].search(
                    [
                        ("from_company_id", "=", self.move_id.company_id.id),
                        ("to_company_id", "in", to_company_ids),
                    ]
                )

                config_details = "\n".join(
                    [
                        f"{config.to_company_id.name} "
                        f"({config.sudo().from_company_debit_account_id.display_name})"
                        for config in intercompany_trans_account_config_recs
                    ]
                )

                raise ValidationError(
                    self.env._(
                        "Intercompany Account Configuration:\n\n"
                        "%(intercompany_config_accounts)s\n\n"
                        "The created journal entry contains incorrect "
                        "accounts in its line items.\n"
                        "Please review and correct the accounts "
                        "before proceeding.",
                        intercompany_config_accounts=config_details,
                    )
                )

        self._check_intercompany_transaction_config_missing_fields(
            intercompany_transaction_config_rec
        )

        return intercompany_transaction_config_rec

    @api.onchange("transfer_to_company_id")
    def _onchange_transfer_to_company_id(self) -> None:
        """Update account_id based on intercompany config."""
        for rec in self.filtered(lambda x: x.transfer_to_company_id):
            config = rec._get_move_line_intercompany_transaction_config()
            if config:
                rec.account_id = config.from_company_debit_account_id
