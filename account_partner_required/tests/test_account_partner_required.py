# Copyright 2014-2022 Acsone (http://acsone.eu)
# Copyright 2016-2022 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAccountPartnerRequired(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.account_obj = cls.env["account.account"]
        cls.move_obj = cls.env["account.move"]
        cls.move_line_obj = cls.env["account.move.line"]
        cls.company_id = cls.env.ref("base.main_company").id
        cls.sale_journal = cls.env["account.journal"].create(
            {
                "type": "sale",
                "code": "SJXX",
                "name": "Sale journal",
                "company_id": cls.company_id,
            }
        )
        cls.account1 = cls.account_obj.create(
            {
                "code": "124242",
                "name": "Test 1",
                "account_type": "asset_cash",
                "company_id": cls.company_id,
            }
        )
        cls.account2 = cls.account_obj.create(
            {
                "code": "124243",
                "name": "Test 2",
                "account_type": "asset_receivable",
                "company_id": cls.company_id,
            }
        )
        cls.account3 = cls.account_obj.create(
            {
                "code": "124244",
                "name": "Test 3",
                "account_type": "liability_payable",
                "company_id": cls.company_id,
            }
        )

    def _create_move(self, with_partner, amount=100):
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
        move_line = False
        for line in move.line_ids:
            if line.account_id == self.account2:
                move_line = line
                break
        return move_line

    def test_optional(self):
        self._create_move(with_partner=False)
        self._create_move(with_partner=True)

    def test_always_no_partner(self):
        self.account2.partner_policy = "always"
        with self.assertRaises(ValidationError):
            self._create_move(with_partner=False)

    def test_always_no_partner_0(self):
        # accept missing partner when debit=credit=0
        self.account2.partner_policy = "always"
        self._create_move(with_partner=False, amount=0)

    def test_always_with_partner(self):
        self.account2.partner_policy = "always"
        self._create_move(with_partner=True)

    def test_never_no_partner(self):
        self.account2.partner_policy = "never"
        self._create_move(with_partner=False)

    def test_never_with_partner(self):
        self.account2.partner_policy = "never"
        with self.assertRaises(ValidationError):
            self._create_move(with_partner=True)

    def test_never_with_partner_0(self):
        self.account2.partner_policy = "never"
        # accept partner when debit=credit=0
        self._create_move(with_partner=True, amount=0)

    def test_always_remove_partner(self):
        # remove partner when policy is always
        self.account2.partner_policy = "always"
        line = self._create_move(with_partner=True)
        with self.assertRaises(ValidationError):
            line.write({"partner_id": False})

    def test_change_account(self):
        self.account2.partner_policy = "optional"
        line = self._create_move(with_partner=False)
        # change account to an account with policy always but missing partner
        self.account3.partner_policy = "always"
        with self.assertRaises(ValidationError):
            line.write({"account_id": self.account3.id})
        # change account to an account with policy always with partner
        line.write(
            {
                "account_id": self.account3.id,
                "partner_id": self.env.ref("base.res_partner_1").id,
            }
        )
