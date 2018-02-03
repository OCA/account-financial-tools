# -*- coding: utf-8 -*-
# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.modules.module import get_module_resource


class TestAccountMoveLineImport(TransactionCase):

    def setUp(self):
        super(TestAccountMoveLineImport, self).setUp()
        self.aml_import_model = self.env['aml.import']
        self.am_model = self.env['account.move']
        self.module_name = __name__.split('addons.')[1].split('.')[0]
        ap_type = self.env.ref('account.data_account_type_payable')
        self.env['account.account'].create({
            'code': 'X1111',
            'name': 'Account Payable',
            'user_type_id': ap_type.id,
            'reconcile': True
        })
        self.j_misc = self.env['account.journal'].search(
            [('code', '=', 'MISC')])

    def test_aml_file_import(self):

        am = self.am_model.create({
            'date': fields.Date.today(),
            'journal_id': self.j_misc.id})
        aml_file_path = get_module_resource(
            self.module_name, 'tests',
            'test_account_move_lines.csv')
        aml_data = open(aml_file_path, 'rb').read().encode('base64')
        aml_import = self.aml_import_model.create(
            {'aml_data': aml_data,
             'csv_separator': ';',
             'decimal_separator': ','})
        aml_import.with_context({'active_id': am.id}).aml_import()
        self.assertEquals(am.amount, 5000.00)
