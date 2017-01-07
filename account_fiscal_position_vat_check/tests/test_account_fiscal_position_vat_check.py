# -*- coding: utf-8 -*-
# Copyright 2016 Laurent Bélorgey <lb@lalieutenante.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.tests.common import TransactionCase


class TestAccountFiscalPositionVatCheck(TransactionCase):
    def test_partner_must_have_vat_check(self):
        fp = self.env['account.fiscal.position'].create({
            'name': 'Test',
            'customer_must_have_vat': True})
        customer = self.env['res.partner'].search(
            [('customer', '=', True)], limit=1)
        customer.write({'property_account_position_id': fp.id})
        res = customer.fiscal_position_change()
        self.assertEqual(res['warning']['title'], 'Missing VAT number:')
        fp.write({'customer_must_have_vat': False})
        res = customer.fiscal_position_change()
        self.assertFalse(res)
