# © 2014-2016 Acsone (http://acsone.eu)
# © 2016 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime
from odoo.tests import common
from odoo.exceptions import ValidationError


class TestAccountPartnerRequired(common.TransactionCase):

    def setUp(self):
        super(TestAccountPartnerRequired, self).setUp()
        self.account_obj = self.env['account.account']
        self.account_type_obj = self.env['account.account.type']
        self.move_obj = self.env['account.move']
        self.move_line_obj = self.env['account.move.line']
        self.sale_journal = self.env['account.journal'].create({
            'type': 'sale',
            'code': 'SJXX',
            'name': 'Sale journal',
            })
        liq_acc_type = self.env.ref('account.data_account_type_liquidity')
        self.account1 = self.account_obj.create({
            'code': '124242',
            'name': 'Test 1',
            'user_type_id': liq_acc_type.id,
            })
        self.account_type_custom = self.account_type_obj.create({
            'name': 'acc type test',
            'type': 'other',
            'partner_policy': 'optional',
        })
        self.account2 = self.account_obj.create({
            'code': '124243',
            'name': 'Test 2',
            'user_type_id': self.account_type_custom.id,
            })
        self.account3 = self.account_obj.create({
            'code': '124244',
            'name': 'Test 3',
            'user_type_id': self.account_type_custom.id,
            })

    def _create_move(self, with_partner, amount=100):
        date = datetime.now()
        if with_partner:
            partner_id = self.env.ref('base.res_partner_1').id
        else:
            partner_id = False
        move_vals = {
            'journal_id': self.sale_journal.id,
            'date': date,
            'line_ids': [
                (0, 0, {
                    'name': '/',
                    'debit': 0,
                    'credit': amount,
                    'account_id': self.account1.id,
                    }),
                (0, 0, {
                    'name': '/',
                    'debit': amount,
                    'credit': 0,
                    'account_id': self.account2.id,
                    'partner_id': partner_id,
                    })
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
        self.account_type_custom.partner_policy = 'always'
        with self.assertRaises(ValidationError):
            self._create_move(with_partner=False)

    def test_always_no_partner_0(self):
        # accept missing partner when debit=credit=0
        self.account_type_custom.partner_policy = 'always'
        self._create_move(with_partner=False, amount=0)

    def test_always_with_partner(self):
        self.account_type_custom.partner_policy = 'always'
        self._create_move(with_partner=True)

    def test_never_no_partner(self):
        self.account_type_custom.partner_policy = 'never'
        self._create_move(with_partner=False)

    def test_never_with_partner(self):
        self.account_type_custom.partner_policy = 'never'
        with self.assertRaises(ValidationError):
            self._create_move(with_partner=True)

    def test_never_with_partner_0(self):
        self.account_type_custom.partner_policy = 'never'
        # accept partner when debit=credit=0
        self._create_move(with_partner=True, amount=0)

    def test_always_remove_partner(self):
        # remove partner when policy is always
        self.account_type_custom.partner_policy = 'always'
        line = self._create_move(with_partner=True)
        with self.assertRaises(ValidationError):
            line.write({'partner_id': False})

    def test_change_account(self):
        self.account_type_custom.partner_policy = 'optional'
        line = self._create_move(with_partner=False)
        # change account to an account with policy always but missing partner
        self.account_type_custom.partner_policy = 'always'
        with self.assertRaises(ValidationError):
            line.write({'account_id': self.account3.id})
        # change account to an account with policy always with partner
        line.write({
            'account_id': self.account3.id,
            'partner_id': self.env.ref('base.res_partner_1').id
            })
