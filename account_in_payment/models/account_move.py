# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import config


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def _get_invoice_in_payment_state(self):
        """
        We override this method to change the state of the invoice to in_payment
        when the payment is created from the invoice.
        """
        if config["test_enable"] and not self._context.get(
            "test_get_invoice_in_payment_state"
        ):
            return super()._get_invoice_in_payment_state()
        return "in_payment"
