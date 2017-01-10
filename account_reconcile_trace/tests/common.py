# -*- coding: utf-8 -*-

from openerp.tests import common


class TestCommon(common.TransactionCase):

    def setUp(self):
        super(TestCommon, self).setUp()

        self.ProductObj = self.env['product.product']
        self.PartnerObj = self.env['res.partner']
        self.JournalObj = self.env['account.journal']
        self.ModelDataObj = self.env['ir.model.data']
        self.InvoiceObj = self.env['account.invoice']
        self.MoveObj = self.env['account.move']
        self.MoveLineObj = self.env['account.move.line']
        self.PeriodObj = self.env['account.period']
        self.TraceDirectObj = self.env['account.reconcile.trace.direct']
        self.TraceRecursiveObj = self.env['account.reconcile.trace.direct']

        # Model Data
        self.main_company = self.ModelDataObj.xmlid_to_res_id(
            'base.main_company'
        )
        self.main_customer = self.ModelDataObj.xmlid_to_res_id(
            'base.res_partner_2'
        )
        self.main_supplier = self.ModelDataObj.xmlid_to_res_id(
            'base.res_partner_1'
        )
        self.product_consultant = self.ModelDataObj.xmlid_to_res_id(
            'product.product_product_consultant'
        )
        self.uom_hour = self.ModelDataObj.xmlid_to_res_id(
            'product.product_uom_hour'
        )
        self.debit_journal = self.ModelDataObj.xmlid_to_res_id(
            'account_reconcile_trace.checks_debit_journal'
        )
        self.credit_journal = self.ModelDataObj.xmlid_to_res_id(
            'account_reconcile_trace.checks_credit_journal'
        )
        self.debit_account = self.ModelDataObj.xmlid_to_res_id(
            'account_reconcile_trace.tdd'
        )
        self.credit_account = self.ModelDataObj.xmlid_to_res_id(
            'account_reconcile_trace.tcc'
        )
        self.sales_journal = self.ModelDataObj.xmlid_to_res_id(
            'account.sales_journal'
        )
        self.purchase_journal = self.ModelDataObj.xmlid_to_res_id(
            'account.expenses_journal'
        )
        self.receive_account = self.ModelDataObj.xmlid_to_res_id(
            'account.a_recv'
        )
        self.payable_account = self.ModelDataObj.xmlid_to_res_id(
            'account.a_pay'
        )
        self.sale_account = self.ModelDataObj.xmlid_to_res_id(
            'account.a_sale'
        )
        self.expense_account = self.ModelDataObj.xmlid_to_res_id(
            'account.a_expense'
        )
        self.pay_account_id = self.ModelDataObj.xmlid_to_res_id(
            'account.cash'
        )
        self.journal_id = self.ModelDataObj.xmlid_to_res_id(
            'account.bank_journal'
        )
