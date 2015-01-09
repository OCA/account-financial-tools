# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from mock import MagicMock
from openerp.tests import common


class FixedFeesTester(common.TransactionCase):

    def setUp(self):
        """Initialize credit control level mock to test fees computations"""
        super(FixedFeesTester, self).setUp()
        self.currency_model = self.env['res.currency']
        self.euro = self.currency_model.search([('name', '=', 'EUR')])
        self.assertTrue(self.euro)
        self.usd = self.currency_model.search([('name', '=', 'USD')])
        self.assertTrue(self.usd)

        self.euro_level = MagicMock(name='Euro policy level')
        self.euro_level.dunning_fixed_amount = 5.0
        self.euro_level.dunning_currency_id = self.euro
        self.euro_level.dunning_type = 'fixed'

        self.usd_level = MagicMock(name='USD policy level')
        self.usd_level.dunning_fixed_amount = 5.0
        self.usd_level.dunning_currency_id = self.usd
        self.usd_level.dunning_type = 'fixed'
        self.dunning_model = self.env['credit.control.dunning.fees.computer']

    def test_type_getter(self):
        """Test that correct compute function is returned for "fixed" type"""
        c_fun = self.dunning_model._get_compute_fun('fixed')
        self.assertEqual(c_fun, self.dunning_model.compute_fixed_fees)

    def test_unknow_type(self):
        """Test that non implemented error is raised if invalide fees type"""
        with self.assertRaises(NotImplementedError):
            self.dunning_model._get_compute_fun('bang')

    def test_computation_same_currency(self):
        """Test that fees are correctly computed with same currency"""
        credit_line = MagicMock(name='Euro credit line')
        credit_line.policy_level_id = self.euro_level
        credit_line.currency_id = self.euro
        fees = self.dunning_model.compute_fixed_fees(credit_line)
        self.assertEqual(fees, self.euro_level.dunning_fixed_amount)

    def test_computation_different_currency(self):
        """Test that fees are correctly computed with different currency"""
        credit_line = MagicMock(name='USD credit line')
        credit_line.policy_level_id = self.euro_level
        credit_line.currency_id = self.usd
        fees = self.dunning_model.compute_fixed_fees(credit_line)
        self.assertNotEqual(fees, self.euro_level.dunning_fixed_amount)

    def test_no_fees(self):
        """Test that fees are not generated if no amount defined on level"""
        credit_line = MagicMock(name='USD credit line')
        credit_line.policy_level_id = self.euro_level
        self.euro_level.dunning_fixed_amount = 0.0
        credit_line.currency_id = self.usd
        fees = self.dunning_model.compute_fixed_fees(credit_line)
        self.assertEqual(fees, 0.0)
