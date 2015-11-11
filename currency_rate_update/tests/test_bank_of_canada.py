# -*- coding: utf-8 -*-
##############################################################################
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2015 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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
from unittest2 import TestCase
from openerp.osv.orm import except_orm

from openerp.tests.common import TransactionCase
from openerp.addons.currency_rate_update import currency_rate_update
BankOfCanadaGetter = currency_rate_update.BankOfCanadaGetter


class TestBankOfCanada(TransactionCase):

    def setUp(self):
        """Test the Bank of Canada Service on the main company"""
        super(TestBankOfCanada, self).setUp()
        # Get context
        self.user_model = self.registry("res.users")
        self.context = self.user_model.context_get(self.cr, self.uid)

        currency_cad = self.browse_ref("base.CAD")
        # Set to base currency, must be 1.0
        currency_cad.write({"base": True, "rate_ids": [(0, 0, {"rate": 1.0})]})
        self.company = self.browse_ref("base.main_company")
        self.company.write({
            "auto_currency_up": True,
            "services_to_use": [(0, 0, {
                "service": "BankOfCanadaGetter",
                "currency_to_update": [(6, 0, [
                    self.ref("base.CAD"),
                    self.ref("base.USD"),
                    self.ref("base.EUR"),
                ])],
            })],
        })

    def test_refresh_currency(self):
        self.assertTrue(
            self.registry("res.company").button_refresh_currency(
                self.cr, self.uid, ids=None, context=self.context
            )
        )


class TestBankOfCanadaGetter(TestCase):

    def setUp(self):
        """Test the Bank of Canada Service on the main company"""
        self.getter = BankOfCanadaGetter()

    def test_bad_currency(self):
        """ALL should not be in Bank of Canada's currencies"""
        with self.assertRaises(except_orm):
            self.getter.get_updated_currency(
                currencies=["ALL"],
                main_currency="CAD",
                max_delta_days=4,
            )
