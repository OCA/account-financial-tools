# Copyright 2026 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestJournalBalanceHoot(HttpCase):
    def test_js(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop"
            "&filter=journal%20balances%20stay%20hidden",
            "",
            "",
            login="admin",
            success_signal="[HOOT] Test suite succeeded",
            error_checker=lambda x: "[HOOT]" not in x,
        )
