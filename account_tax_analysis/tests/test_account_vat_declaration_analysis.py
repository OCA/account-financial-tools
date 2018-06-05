# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountVatDeclarationAnalysis(TransactionCase):

    def setUp(self):
        super(TestAccountVatDeclarationAnalysis, self).setUp()

    def test_1(self):
        wiz = self.env["account.vat.declaration.analysis"].new()

        wiz.start_date = "2017-01-01"
        wiz.end_date = "2017-01-30"

        self.assertEqual(
            wiz.show_vat()["domain"],
            [('date', '>=', '2017-01-01'), ('date', '<=', '2017-01-30')])

        company = self.env.user.company_id
        wiz.company_id = company

        self.assertEqual(
            wiz.show_vat()["domain"],
            [('date', '>=', '2017-01-01'), ('date', '<=', '2017-01-30'),
             ("company_id", "=", company.id)])

        wiz.target_move = "all"
        self.assertEqual(
            wiz.show_vat()["context"],
            {'search_default_group_by_tax_type': 1})

        wiz.target_move = "posted"
        self.assertEqual(
            wiz.show_vat()["context"],
            {'search_default_group_by_tax_type': 1,
             'search_default_posted': 1})
