# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    code = fields.Char(size=6)

    @api.depends("type", "currency_id")
    def _compute_inbound_payment_method_line_ids(self):
        """Set payment account for manual inbound payment methods.

        Performance optimization:
        - Filter bank journals early
        - Cache payment account lookup
        - Batch write operations
        """
        res = super()._compute_inbound_payment_method_line_ids()

        bank_journals = self.filtered(lambda j: j.type == "bank")
        if not bank_journals:
            return res

        for journal in bank_journals:
            manual_lines = journal.inbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id.code == "manual"
            )
            if manual_lines:
                payment_account = journal.company_id.inbound_payment_account_id
                if payment_account:
                    manual_lines.write({"payment_account_id": payment_account.id})

        return res

    @api.depends("type", "currency_id")
    def _compute_outbound_payment_method_line_ids(self):
        """Set payment account for manual outbound payment methods.

        Performance optimization:
        - Filter bank journals early
        - Cache payment account lookup
        - Batch write operations
        """
        res = super()._compute_outbound_payment_method_line_ids()

        bank_journals = self.filtered(lambda j: j.type == "bank")
        if not bank_journals:
            return res

        for journal in bank_journals:
            manual_lines = journal.outbound_payment_method_line_ids.filtered(
                lambda line: line.payment_method_id.code == "manual"
            )
            if manual_lines:
                payment_account = journal.company_id.outbound_payment_account_id
                if payment_account:
                    manual_lines.write({"payment_account_id": payment_account.id})

        return res
