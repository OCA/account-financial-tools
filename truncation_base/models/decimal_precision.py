# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from decimal import ROUND_DOWN, Decimal

from odoo import api, models


class DecimalPrecision(models.Model):
    _inherit = "decimal.precision"

    @api.model
    def truncate(self, value, application, currency=None):
        """Truncate ``value`` at the ``application`` named precision.

        Monetary fields silently round their value to the currency's own
        precision on every write, which would erase any truncation done at
        a finer precision. Pass the record's ``currency`` so the effective
        precision never exceeds what the Monetary field can actually store.
        """
        precision_digits = self.precision_get(application)
        if currency:
            precision_digits = min(precision_digits, currency.decimal_places)
        exponent = Decimal(1).scaleb(-precision_digits)
        return float(Decimal(str(value)).quantize(exponent, rounding=ROUND_DOWN))
