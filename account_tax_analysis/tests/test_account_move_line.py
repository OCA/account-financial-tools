# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestAccountMoveLine(TransactionCase):

    def setUp(self):
        super(TestAccountMoveLine, self).setUp()

        acc_tax = self.env["account.tax"]
        self.tax1 = acc_tax.create({
            "name": "tax1",
            "amount": 1,
        })

        self.move_line_tax_line_id = self.env["account.move.line"].search(
            [("tax_line_id", "!=", False)], limit=1)
        self.move_line_tax_ids = self.env["account.move.line"].search(
            [("tax_ids", "!=", False)], limit=1)

    def test_analysis_tax(self):

        self.assertEqual(self.move_line_tax_line_id.analysis_tax,
                         self.move_line_tax_line_id.tax_line_id.analysis_name)

        current_tax = self.move_line_tax_ids.tax_ids
        self.assertEqual(self.move_line_tax_ids.analysis_tax,
                         current_tax.analysis_name)

        self.move_line_tax_ids.tax_ids += self.tax1
        self.assertEqual(self.move_line_tax_ids.analysis_tax,
                         "%s, tax1" % current_tax.analysis_name)

    def test_analysis_name(self):
        self.assertEqual(self.tax1.analysis_name, "tax1")

        self.tax1.description = "tax1_d"
        self.assertEqual(self.tax1.analysis_name, "tax1_d - tax1")
