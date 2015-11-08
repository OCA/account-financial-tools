# -*- coding: utf-8 -*-
##############################################################################
#
#    Authors: Adrien Peiffer, Laetitia Gangloff
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
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

import openerp.tests.common as common
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import workflow

import time


def create_simple_invoice(self):
    partner_id = self.ref('base.res_partner_2')
    product_id = self.ref('product.product_product_4')
    today = datetime.now()
    journal_id = self.ref('account.sales_journal')
    date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
    return self.env['account.invoice']\
        .create({'partner_id': partner_id,
                 'account_id':
                 self.ref('account.a_recv'),
                 'journal_id':
                 journal_id,
                 'date_invoice': date,
                 'invoice_line': [(0, 0, {'name': 'test',
                                          'account_id':
                                          self.ref('account.a_sale'),
                                          'price_unit': 2000.00,
                                          'quantity': 1,
                                          'product_id': product_id,
                                          }
                                   )
                                  ],
                 })


def create_simple_bank_statement(self):
    return self.env['account.bank.statement'].create({
        'journal_id': self.ref("account.bank_journal"),
        'date': time.strftime('%Y') + '-07-15',
        'balance_end_real': 42,
        'line_ids': [(0, 0, {'name': 'my payment',
                             'partner_id': self.ref('base.res_partner_2'),
                             'amount': 42,
                             'date': time.strftime('%Y') + '-07-15',
                             'account_id': self.ref('account.bnk')
                             })]
    })


class TestAccountDefaultDraftMove(common.TransactionCase):

    def setUp(self):
        super(TestAccountDefaultDraftMove, self).setUp()

    def test_draft_move_invoice(self):
        invoice = create_simple_invoice(self)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        self.assertEqual(invoice.move_id.state, 'draft', 'State error!')

    def test_draft_move_statement(self):
        statement = create_simple_bank_statement(self)
        statement.button_confirm_bank()
        self.assertEqual(statement.move_line_ids[0].move_id.state,
                         'draft', 'State error!')

    def test_config_move_invoice(self):
        # update configuration to take account of the journal settings
        self.env['ir.config_parameter'].set_param('use_journal_setting', True)
        # set entry posted to False
        journal = self.env['account.journal'].browse(
            self.ref('account.sales_journal'))
        journal.entry_posted = False
        invoice = create_simple_invoice(self)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        self.assertEqual(invoice.move_id.state, 'draft', 'State error!')

        journal.entry_posted = True
        invoice = create_simple_invoice(self)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        self.assertEqual(invoice.move_id.state, 'posted', 'State error!')

    def test_config_move_statement(self):
        # update configuration to take account of the journal settings
        self.env['ir.config_parameter'].set_param('use_journal_setting', True)
        # set entry posted to False
        journal = self.env['account.journal'].browse(
            self.ref('account.bank_journal'))
        journal.entry_posted = False
        statement = create_simple_bank_statement(self)
        statement.button_confirm_bank()
        self.assertEqual(statement.move_line_ids[0].move_id.state,
                         'draft', 'State error!')

        journal.entry_posted = True
        statement = create_simple_bank_statement(self)
        statement.button_confirm_bank()
        self.assertEqual(statement.move_line_ids[0].move_id.state,
                         'posted', 'State error!')
