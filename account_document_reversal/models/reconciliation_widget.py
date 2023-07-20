# Copyright 2023 ForgeFlow, S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountReconciliation(models.AbstractModel):
    _inherit = "account.reconciliation.widget"

    def _search_domain_payment_reconciliation_to_remove(self, domain):
        start_index = domain.index(("statement_line_id", "=", False))
        end_index = domain.index(("balance", "!=", 0.0)) + 1
        return start_index, end_index

    @api.model
    def _domain_move_lines_for_reconciliation(
        self,
        st_line,
        aml_accounts,
        partner_id,
        excluded_ids=None,
        search_str=False,
        mode="rp",
    ):
        domain = super()._domain_move_lines_for_reconciliation(
            st_line,
            aml_accounts,
            partner_id,
            excluded_ids=excluded_ids,
            search_str=search_str,
            mode=mode,
        )
        aml_accounts = [
            st_line.journal_id.default_credit_account_id.id,
            st_line.journal_id.default_debit_account_id.id,
        ]
        try:
            (
                start_index,
                end_index,
            ) = self._search_domain_payment_reconciliation_to_remove(domain)
        except ValueError as e:
            raise ValidationError(
                _(
                    "Could not implement the restriction to remove "
                    "reversed payments: %s"
                )
                % str(e)
            )

        domain_reconciliation_to_add = [
            "&",
            ("statement_line_id", "=", False),
            ("account_id", "in", aml_accounts),
            ("payment_id", "<>", False),
            ("balance", "!=", 0.0),
            ("payment_id.state", "!=", "cancelled"),
        ]
        if start_index and end_index:
            domain[start_index:end_index] = domain_reconciliation_to_add
        return domain
