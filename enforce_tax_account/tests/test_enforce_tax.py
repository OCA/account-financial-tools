# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 Bringsvor Consulting AS. All rights reserved.
#    @author Torvald B. Bringsvor
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp.tests import common
from openerp import fields, _
from datetime import datetime

class test_enforce_tax_account(common.TransactionCase):

    def setUp(self):
        super(test_enforce_tax_account, self).setUp()
        self.moveline = self.env['account.move.line']
        self.journal = self.env['account.journal'].search([])[0]
        self.period = self.env['account.period'].search([('company_id','=',self.journal.company_id.id)])[0]
        self.account = self.env['account.account'].search([('code','!=',''), ('type','=','other'),('company_id','=',self.journal.company_id.id)])[0]
        self.tax_code = self.env['account.tax.code'].search([('company_id','=',self.journal.company_id.id)])[0]
        self.other_tax_code = self.env['account.tax.code'].search([('id','!=',self.tax_code.id), ('company_id','=',self.journal.company_id.id)])[0]

    def test_create_fail_no_account(self):
        with self.assertRaises(Warning) as cm:
            self.moveline.create({})

    def test_create_fail_when_no_tax(self):
        #self.account.write({'force_tax_id': self.tax_code.id})
        self.account.force_tax_id = self.tax_code
        val = {'debit': 100.0,
               'date': fields.Date.today(),
               'name': 'Test Entry - should fail',
               'company_id': self.period.company_id.id,
               'account_id' : self.account.id,
            'credit': 0.0,
            'journal_id': self.journal.id,
            'period_id': self.period.id,
            }
        with self.assertRaises(Warning) as cm:
            self.moveline.create(val)

        the_exception = cm.exception
        expected_args = _('Missing value'), _('Tax code must be set on accounting move lines on account %s' % self.account.code)
        self.assertEqual(the_exception.args, expected_args)

    def test_create_fail_when_wrong_tax(self):
        #self.account.write({'force_tax_id': self.tax_code.id})
        self.account.force_tax_id = self.tax_code
        val = {'debit': 100.0,
               'date': fields.Date.today(),
               'name': 'Test Entry - should fail',
               'company_id': self.period.company_id.id,
               'account_id' : self.account.id,
               'tax_code_id': self.other_tax_code.id,
            'credit': 0.0,
            'journal_id': self.journal.id,
            'period_id': self.period.id,
            }
        with self.assertRaises(Warning) as cm:
            self.moveline.create(val)

        the_exception = cm.exception

        expected_args = _('Wrong value'), _('Account %s is set to force tax code "%s" but got a moveline with "%s"' % (self.account.code, self.tax_code.name, self.other_tax_code.name))
        self.assertEqual(the_exception.args, expected_args)


    def test_write_fail_when_wrong_vat(self):
        self.account.force_tax_id = self.tax_code
        val = {'debit': 100.0,
               'date': fields.Date.today(),
               'name': 'Test Entry - should fail',
               'company_id': self.period.company_id.id,
               'account_id' : self.account.id,
               'tax_code_id': self.tax_code.id,
            'credit': 0.0,
            'journal_id': self.journal.id,
            'period_id': self.period.id,
            }
        ml = self.moveline.create(val)

        with self.assertRaises(Warning) as cm:
            ml.write({'tax_code_id': self.other_tax_code.id})

        the_exception = cm.exception
        expected_args = _('Wrong value'), _('Account %s is set to force tax code "%s" but got a moveline with "%s"' % (self.account.code, self.tax_code.name, self.other_tax_code.name))
        self.assertEqual(the_exception.args, expected_args)

