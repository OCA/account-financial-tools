# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.base.tests.common import BaseCommon


class TestTruncationBase(BaseCommon):
    def test_truncate_cuts_off_extra_decimals_without_rounding(self):
        precision = self.env["decimal.precision"].create(
            {"name": "Test Truncation Precision", "digits": 4}
        )
        # 47.41659 would round up to 47.4166 at 4 digits; truncation must
        # instead drop the extra decimals.
        self.assertEqual(
            self.env["decimal.precision"].truncate(47.41659, precision.name),
            47.4165,
        )

    def test_truncate_towards_zero_on_negative_values(self):
        precision = self.env["decimal.precision"].create(
            {"name": "Test Truncation Precision Negative", "digits": 2}
        )
        # Truncation cuts towards zero, unlike floor which would give -1.24.
        self.assertEqual(
            self.env["decimal.precision"].truncate(-1.239, precision.name),
            -1.23,
        )

    def test_truncate_unknown_application_defaults_to_two_digits(self):
        self.assertEqual(
            self.env["decimal.precision"].truncate(1.23456, "Does Not Exist"),
            1.23,
        )

    def test_truncate_clamps_to_currency_precision(self):
        precision = self.env["decimal.precision"].create(
            {"name": "Test Truncation Currency Precision", "digits": 4}
        )
        currency = self.env.ref("base.USD")
        # The named precision allows 4 digits, but a Monetary field would
        # silently round the value back to the currency's own 2 digits on
        # every write, so the truncation must already happen at that
        # coarser precision to have any real effect.
        self.assertEqual(
            self.env["decimal.precision"].truncate(
                47.41659, precision.name, currency=currency
            ),
            47.41,
        )

    def test_partner_truncate_subtotal_defaults_to_false(self):
        partner = self.env["res.partner"].create({"name": "Truncation Test Partner"})
        self.assertFalse(partner.truncate_subtotal)
