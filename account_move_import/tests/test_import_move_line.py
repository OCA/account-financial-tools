# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tests.common import TransactionCase
from openerp.modules.module import get_module_resource


class TestAccountMoveLineImport(TransactionCase):

    def setUp(self):
        super(TestAccountMoveLineImport, self).setUp()
        cr, uid = self.cr, self.uid
        self.aml_import_model = self.registry('aml.import')
        self.am_model = self.registry('account.move')
        self.am_id = self.registry('ir.model.data').get_object_reference(
            cr, uid, 'account_move_import', 'am_0')[1]

    def test_aml_file_import(self):
        cr, uid = self.cr, self.uid
        aml_file_path = get_module_resource(
            'account_move_import', 'tests',
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
