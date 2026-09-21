# Copyright 2026 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends("journal_id", "payment_method_code")
    def _compute_check_number(self):
        options = self.env["ir.sequence.option.line"].get_model_options(self._name)

        payment_sequence_map = {}
        for pay in self:
            if (
                pay.payment_method_code == "check_printing"
                and not pay.journal_id.check_manual_sequencing
            ):
                sequence = self.env["ir.sequence.option.line"].get_sequence(
                    pay, options=options
                )
                if sequence:
                    payment_sequence_map[pay] = sequence

        for pay, sequence in payment_sequence_map.items():
            pay.check_number = sequence.get_next_char(sequence.number_next_actual)

        payments_without_sequence = self.filtered(
            lambda p: p not in payment_sequence_map
        )
        if payments_without_sequence:
            super(AccountPayment, payments_without_sequence)._compute_check_number()
        return

    def print_checks(self):
        res = super().print_checks()
        if isinstance(res, dict):
            options = self.env["ir.sequence.option.line"].get_model_options(self._name)

            payment_sequence_map = {}
            for payment in self:
                sequence = self.env["ir.sequence.option.line"].get_sequence(
                    payment, options=options
                )
                if sequence:
                    payment_sequence_map[payment] = sequence

            if payment_sequence_map:
                for payment, sequence in payment_sequence_map.items():
                    payment.check_number = sequence.next_by_id()

                payments_with_sequence = self.filtered(
                    lambda r: r in payment_sequence_map
                )
                payments_with_sequence.filtered(
                    lambda r: r.state == "draft"
                ).action_post()

                return payments_with_sequence.do_print_checks()
        return res
