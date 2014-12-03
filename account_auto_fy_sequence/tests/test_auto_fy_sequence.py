# coding=utf-8
##############################################################################
#
#    account_auto_fy_sequence module for Odoo
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
#
#    account_auto_fy_sequence is free software:
#    you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    account_auto_fy_sequence is distributed
#    in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time

import openerp.tests.common as common
from openerp.osv import orm


class TestAutoFYSequence(common.TransactionCase):

    def setUp(self):
        super(TestAutoFYSequence, self).setUp()
        self.seq_obj = self.registry('ir.sequence')

    def _create_seq(self, prefix):
        seq_id = self.seq_obj.create(self.cr, self.uid, {
            'name': 'test sequence',
            'implementation': 'no_gap',
            'prefix': prefix,
        })
        return seq_id

    def test_0(self):
        """ normal sequence """
        seq_id = self._create_seq('SEQ/%(year)s/')
        n = self.seq_obj._next(self.cr, self.uid, [seq_id])
        self.assertEqual(n, "SEQ/%s/1" % time.strftime("%Y"))

    def test_1(self):
        """ invoke fiscal year sequence
        without specifying the fiscal year """
        seq_id = self._create_seq('SEQ/%(fy)s/')
        with self.assertRaises(orm.except_orm):
            self.seq_obj._next(self.cr, self.uid, [seq_id])

    def test_2(self):
        """ invoke fiscal year sequence """
        fiscalyear_id = self.ref('account.data_fiscalyear')
        context = {'fiscalyear_id': fiscalyear_id}
        fiscalyear = self.registry('account.fiscalyear')\
            .browse(self.cr, self.uid, fiscalyear_id)
        seq_id = self._create_seq('SEQ/%(fy)s/')
        n = self.seq_obj._next(self.cr, self.uid, [seq_id], context)
        self.assertEqual(n, "SEQ/%s/1" % fiscalyear.code)
        n = self.seq_obj._next(self.cr, self.uid, [seq_id], context)
        self.assertEqual(n, "SEQ/%s/2" % fiscalyear.code)

    def test_3(self):
        """ Create journal and check the sequence attached to the journal """
        aj_obj = self.registry('account.journal')
        aj_id = aj_obj.create(self.cr, self.uid, {'name': 'sequence (test)',
                                                  'code': 'SQT',
                                                  'type': 'bank',
                                                  })
        aj = aj_obj.browse(self.cr, self.uid, aj_id)
        self.assertEqual(aj.sequence_id.prefix, 'SQT/%(fy)s/')
