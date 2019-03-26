# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo.addons.hr_expense.tests.common import TestExpenseCommon


class TestMoveRefExpense(TestExpenseCommon):

    @classmethod
    def setUpClass(self):
        super(TestMoveRefExpense, self).setUpClass()
        self.setUpAdditionalAccounts()
        self.product_expense = self.env['product.product'].create({
            'name': "Delivered at cost",
            'standard_price': 700,
            'list_price': 700,
            'type': 'consu',
            'supplier_taxes_id': [(6, 0, [self.tax.id])],
            'default_code': 'CONSU-DELI-COST',
            'taxes_id': False,
            'property_account_expense_id': self.account_expense.id,
        })

    def test_expense(self):
        """ Check account move can link back to expense sheet """
        expense = self.env['hr.expense.sheet'].create({
            'name': 'Expense for John Smith',
            'employee_id': self.employee.id,
        })
        expense_line = self.env['hr.expense'].create({
            'name': 'Car Travel Expenses',
            'employee_id': self.employee.id,
            'product_id': self.product_expense.id,
            'unit_amount': 700.00,
            'tax_ids': [(6, 0, [self.tax.id])],
            'sheet_id': expense.id,
            'analytic_account_id': self.analytic_account.id,
        })
        expense_line._onchange_product_id()
        expense.action_submit_sheet()
        expense.approve_expense_sheets()
        # Create Expense Entries
        expense.action_sheet_move_create()
        # Test
        self.assertEqual(expense.account_move_id.document_id, expense,
                         'Document ID not equal to its expense sheet')
        self.assertEqual(expense.account_move_id.document_ref,
                         expense.display_name,
                         'Document Ref not equal to its expense sheet')
