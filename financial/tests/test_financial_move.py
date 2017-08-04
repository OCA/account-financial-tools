# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
#   Hendrix Costa <hendrix.costa@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.addons.financial.tests.financial_test_classes import \
    FinancialTestCase


class ManualFinancialProcess(FinancialTestCase):

    def setUp(self):
        super(ManualFinancialProcess, self).setUp()

    def test_01_check_return_views(self):
        """Check if view is correctly called for python code"""

        # test for  len(financial.move) == 1
        financial_move_id = self.financial_model.search([], limit=1)
        action = financial_move_id.action_view_financial('2receive')
        self.assertEqual(
            action.get('display_name'),
            'financial.move.debt.2receive.form (in financial)')
        self.assertEqual(
            action.get('res_id'), financial_move_id.id)

        action = financial_move_id.action_view_financial('2pay')
        self.assertEqual(
            action.get('display_name'),
            'financial.move.debt.2pay.form (in financial)')
        self.assertEqual(
            action.get('res_id'), financial_move_id.id)

        # test for  len(financial.move) > 1
        financial_move_id = self.financial_model.search([], limit=2)
        action = financial_move_id.action_view_financial('2pay')
        self.assertEqual(action.get('domain')[0][2], financial_move_id.ids)

        # test for  len(financial.move) < 1
        action = self.financial_model.action_view_financial('2pay')
        self.assertEqual(action.get('type'), 'ir.actions.act_window_close')
