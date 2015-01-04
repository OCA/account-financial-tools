# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
import time

import openerp.tests.common as test_common
from openerp import addons


class TestMoveLineImporter(test_common.SingleTransactionCase):

    def get_file(self, filename):
        """Retrieve file from test data,
           encode it as base64
           and adjust it for current year
        """
        path = addons.get_module_resource('async_move_line_importer',
                                          'tests', 'data', filename)
        test_data = open(path).read()
        test_data = test_data.replace('2014', time.strftime('%Y'))
        return test_data.encode("base64")

    def setUp(self):
        super(TestMoveLineImporter, self).setUp()
        self.importer_model = self.registry('move.line.importer')
        self.move_model = self.registry('account.move')

    def tearDown(self):
        super(TestMoveLineImporter, self).tearDown()

    def test_01_one_line_without_orm_bypass(self):
        """Test one line import without bypassing orm"""
        cr, uid = self.cr, self.uid
        importer_id = self.importer_model.create(
            cr, uid,
            {'file': self.get_file('one_move.csv'),
             'delimiter': ';'}
        )
        importer = self.importer_model.browse(cr, uid, importer_id)
        self.assertTrue(importer.company_id, 'Not default company set')
        self.assertFalse(importer.bypass_orm, 'Bypass orm must not be active')
        self.assertEqual(importer.state, 'draft')
        head, data = self.importer_model._parse_csv(cr, uid, importer.id)
        self.importer_model._load_data(
            cr, uid, importer.id, head, data, _do_commit=False, context={})
        importer = self.importer_model.browse(cr, uid, importer_id)
        self.assertEquals(importer.state, 'done',
                          'Exception %s during import' % importer.report)
        created_move_ids = self.move_model.search(
            cr, uid,
            [('ref', '=', 'éöüàè_test_1')]
        )
        self.assertTrue(created_move_ids, 'No move imported')
        created_move = self.move_model.browse(cr, uid, created_move_ids[0])
        self.assertTrue(len(created_move.line_id) == 3,
                        'Wrong number of move line imported')
        debit = credit = 0.0
        for line in created_move.line_id:
            debit += line.debit if line.debit else 0.0
            credit += line.credit if line.credit else 0.0
        self.assertEqual(debit, 1200.00)
        self.assertEqual(credit, 1200.00)
        self.assertEqual(created_move.state, 'draft', 'Wrong move state')

    def test_02_one_line_using_orm_bypass(self):
        """Test one line import using orm bypass"""
        cr, uid = self.cr, self.uid
        importer_id = self.importer_model.create(
            cr, uid,
            {'file': self.get_file('one_move2.csv'),
             'delimiter': ';',
             'bypass_orm': True}
        )
        importer = self.importer_model.browse(cr, uid, importer_id)
        self.assertTrue(importer.company_id, 'Not default company set')
        self.assertTrue(importer.bypass_orm, 'Bypass orm must be active')
        self.assertEqual(importer.state, 'draft')
        head, data = self.importer_model._parse_csv(cr, uid, importer.id)
        context = {'async_bypass_create': True,
                   'company_id': 1}
        self.importer_model._load_data(cr, uid, importer.id, head, data,
                                       _do_commit=False, context=context)
        importer = self.importer_model.browse(cr, uid, importer_id)
        self.assertEquals(importer.state, 'done',
                          'Exception %s during import' % importer.report)
        created_move_ids = self.move_model.search(cr, uid,
                                                  [('ref', '=', 'test_2')])
        self.assertTrue(created_move_ids, 'No move imported')
        created_move = self.move_model.browse(cr, uid, created_move_ids[0])
        self.assertTrue(len(created_move.line_id) == 3,
                        'Wrong number of move line imported')
        debit = credit = 0.0
        for line in created_move.line_id:
            debit += line.debit if line.debit else 0.0
            credit += line.credit if line.credit else 0.0
        self.assertEqual(debit, 1200.00)
        self.assertEqual(credit, 1200.00)
        self.assertEqual(created_move.state, 'draft', 'Wrong move state')

    def test_03_one_line_failing(self):
        """Test one line import with faulty CSV file"""
        cr, uid = self.cr, self.uid
        importer_id = self.importer_model.create(
            cr, uid,
            {'file': self.get_file('faulty_moves.csv'),
             'delimiter': ';'}
        )
        importer = self.importer_model.browse(cr, uid, importer_id)
        self.assertTrue(importer.company_id, 'Not default company set')
        self.assertFalse(importer.bypass_orm, 'Bypass orm must not be active')
        self.assertEqual(importer.state, 'draft')
        head, data = self.importer_model._parse_csv(cr, uid, importer.id)
        self.importer_model._load_data(cr, uid, importer.id, head, data,
                                       _do_commit=False, context={})
        importer = self.importer_model.browse(cr, uid, importer_id)
        self.assertEquals(importer.state, 'error',
                          'No exception %s during import' % importer.report)
        created_move_ids = self.move_model.search(cr, uid,
                                                  [('ref', '=', 'test_3')])
        self.assertFalse(created_move_ids,
                         'Move was imported but it should not be the case')
