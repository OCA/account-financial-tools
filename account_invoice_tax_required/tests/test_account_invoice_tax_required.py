# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo import exceptions


class TestAccountInvoiceTaxRequired(TransactionCase):

    def setUp(self):
        super(TestAccountInvoiceTaxRequired, self).setUp()

        self.account_invoice = self.env['account.invoice']
        self.account_journal = self.env['account.journal']
        self.journal = self.account_journal.create({
            'code': 'test',
            'name': 'test',
            'type': 'sale'
        })
        self.partner = self.env.ref('base.res_partner_3')
        account_user_type = self.env.ref(
            'account.data_account_type_receivable')

        self.account_account = self.env['account.account']
        self.account_rec1_id = self.account_account.create(dict(
            code="cust_acc",
            name="customer account",
            user_type_id=account_user_type.id,
            reconcile=True,
        ))
        self.product_product = self.env['product.product']
        self.product = self.product_product.create({
            'name': 'Test',
            'categ_id': self.env.ref(
                "product.product_category_all").id,
            'standard_price': 50,
            'list_price': 100,
            'type': 'service',
            'uom_id': self.env.ref("product.product_uom_unit").id,
            'uom_po_id': self.env.ref("product.product_uom_unit").id,
            'description': 'Test',
        })

        invoice_line_data = [(0, 0, {
            'product_id': self.product.id,
            'quantity': 10.0,
            'account_id': self.account_account.search(
                [('user_type_id',
                  '=',
                  self.env.ref('account.data_account_type_revenue').id)
                 ], limit=1).id,
            'name': 'product test 5',
            'price_unit': 100.00,
        })]

        self.invoice = self.account_invoice.create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            journal_id=self.journal.id,
            partner_id=self.partner.id,
            account_id=self.account_rec1_id.id,
            invoice_line_ids=invoice_line_data
        ))

    def test_exception(self):
        """Validate invoice without tax must raise exception
        """
        self.invoice.action_date_assign()
        self.invoice.action_move_create()
        with self.assertRaises(exceptions.Warning):
            self.invoice.with_context(
                test_tax_required=True).invoice_validate()
