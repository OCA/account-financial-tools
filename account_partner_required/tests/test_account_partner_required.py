from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPartnerRequired(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.account = cls.env["account.account"].create(
            {
                "code": "ACC01",
                "name": "Test Account",
                "account_type": "expense",
            }
        )

    def _create_and_post_move(self, with_partner, amount=100):
        if with_partner:
            partner_id = self.env.ref("base.res_partner_1").id
        else:
            partner_id = False
        move_vals = {
            "company_id": self.company_id,
            "journal_id": self.sale_journal.id,
            "line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "/",
                        "debit": 0,
                        "credit": amount,
                        "account_id": self.account1.id,
                    },
                ),
                (
                    0,
                    0,
                    {
                        "name": "/",
                        "debit": amount,
                        "credit": 0,
                        "account_id": self.account2.id,
                        "partner_id": partner_id,
                    },
                ),
            ],
        }
        move = self.move_obj.create(move_vals)
        move.action_post()
        move_line = False
        for line in move.line_ids:
            if line.account_id == self.account2:
                move_line = line
                break
        return move_line

    def test_optional(self):
        self._create_and_post_move(with_partner=False)
        self._create_and_post_move(with_partner=True)

        with self.assertRaises(ValidationError):
            self._create_and_post_move(with_partner=False)

    def test_always_no_partner_0(self):
        # accept missing partner when debit=credit=0
        self.account2.partner_policy = "always"
        self._create_and_post_move(with_partner=False, amount=0)

    def test_always_with_partner(self):
        self.account2.partner_policy = "always"
        self._create_and_post_move(with_partner=True)

    def test_never_no_partner(self):
        self.account2.partner_policy = "never"
        self._create_and_post_move(with_partner=False)

    def test_never_with_partner(self):
        self.account2.partner_policy = "never"
        with self.assertRaises(ValidationError):
            self._create_and_post_move(with_partner=True)

    def test_never_with_partner_0(self):
        self.account2.partner_policy = "never"
        # accept partner when debit=credit=0
        self._create_and_post_move(with_partner=True, amount=0)
