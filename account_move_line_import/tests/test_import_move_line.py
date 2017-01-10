# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import TransactionCase
from openerp.modules.module import get_module_resource


class TestAccountMoveLineImport(TransactionCase):

    def setUp(self):
        super(TestAccountMoveLineImport, self).setUp()
        cr, uid = self.cr, self.uid
        self.aml_import_model = self.registry('aml.import')
        self.am_model = self.registry('account.move')
        self.module_name = __name__.split('addons.')[1].split('.')[0]
        self.am_id = self.registry('ir.model.data').get_object_reference(
            cr, uid, self.module_name, 'am_0')[1]

    def test_aml_file_import(self):
        cr, uid = self.cr, self.uid
        aml_file_path = get_module_resource(
            self.module_name, 'tests',
            'test_account_move_lines.csv')
        aml_data = open(aml_file_path, 'rb').read().encode('base64')
        aml_import_id = self.aml_import_model.create(
            cr, uid,
            {'aml_data': aml_data,
             'csv_separator': ';',
             'decimal_separator': ','})
        self.aml_import_model.aml_import(
            cr, uid, [aml_import_id], {'active_id': self.am_id})
        am = self.am_model.browse(cr, uid, self.am_id)
        self.assertEquals(am.amount, 5000.00)
