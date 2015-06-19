# -*- coding: utf-8 -*-
#
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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
#

import openerp.tests.common as common
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import workflow, exceptions


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


class TestAccountConstraints(common.TransactionCase):

    def setUp(self):
        super(TestAccountConstraints, self).setUp()

    def test_draft_move_invoice(self):
        invoice = create_simple_invoice(self)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        move = invoice.move_id
        move_lines = move.line_id
        move.with_context({'from_parent_object': True})\
            .write({'state': 'draft'})
        self.assertRaises(exceptions.Warning, move_lines.write,
                          {'credit': 0.0})

    def test_post_move_invoice_ref(self):
        invoice = create_simple_invoice(self)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        move_lines = invoice.move_id.line_id
        # here, normally no exception is raised in standard code.
        # It's just to verify if it's
        # possible to modify ref field in a post account_move_line
        move_lines.with_context({'from_parent_object': True})\
            .write({'ref': 'test'})

    def test_post_move_invoice(self):
        invoice = create_simple_invoice(self)
        workflow.trg_validate(self.uid, 'account.invoice', invoice.id,
                              'invoice_open', self.cr)
        move_lines = invoice.move_id.line_id
        self.assertRaises(exceptions.Warning, move_lines.write,
                          {'ref': 'test'})
