# -*- coding: utf-8 -*-
# © 2014, Adrien Peiffer, Acsone SA/NV (http://www.acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import openerp.tests.common as common
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import workflow, exceptions


def create_simple_invoice(self):
    partner_id = self.ref('base.res_partner_2')
    product_id = self.ref('product.product_product_4')
    today = datetime.now()
    journal_id = self.env['account.journal'].search([('type','=','sale')])[0]
    account_id = self.env['account.account'].search([('internal_type','=','receivable')])[0]
    account_id_other = self.env['account.account'].search([('internal_type','=','other')])[0]
    
    date = today.strftime(DEFAULT_SERVER_DATE_FORMAT)
    return self.env['account.invoice']\
        .create({'partner_id': partner_id,
                 'account_id': account_id,
                 'journal_id': journal_id.id,
                 'date_invoice': date,
                 'invoice_line': [(0, 0, {'name': 'test',
                                          'account_id':
                                          account_id_other.id,
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
