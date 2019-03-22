# Copyright 2019 Avoin.Systems
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import odoo.tests.common as common
from odoo.tests.common import TransactionCase
from odoo.models import ValidationError


class TestResPartnerBank(TransactionCase):

    def setUp(self):
        super(TestResPartnerBank, self).setUp()
        self.BankAccountObj = self.env['res.partner.bank']
        self.bank_account_1 = self.env.ref('base.bank_partner_demo')
        self.partner_2 = self.env.ref('base.res_partner_2')

    def test_01_duplicate_number_no_override(self):
        with self.assertRaises(ValidationError):
            self.BankAccountObj.create({
                'partner_id': self.partner_2.id,
                'acc_number': self.bank_account_1.acc_number
            })

    def test_02_duplicate_number_override(self):
        self.bank_account_1.override_uniqueness = True
        bank_account_2 = self.BankAccountObj.create({
            'partner_id': self.partner_2.id,
            'acc_number': self.bank_account_1.acc_number
        })

        self.assertEqual(self.bank_account_1.acc_number,
                         bank_account_2.acc_number)
