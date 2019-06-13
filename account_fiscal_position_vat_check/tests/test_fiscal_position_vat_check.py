# Copyright 2018 Raf Ven <raf.ven@dynapps.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestFiscalPositionVatCheck(TransactionCase):

    # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super(TestFiscalPositionVatCheck, self).setUp()
        self._create_fiscal_positions()
        self._create_partners()
        self._configure_accounting()

    def _create_fiscal_positions(self):
        self.fp_b2c = self.env['account.fiscal.position'].create(dict(
            name="EU-VAT-B2C",
            vat_required=False,
        ))
        self.fp_b2b = self.env['account.fiscal.position'].create(dict(
            name="EU-VAT-B2B",
            vat_required=True,
        ))

    def _create_partners(self):
        self.partner_b2c = self.env['res.partner'].create(dict(
            name="Test Partner B2C",

        ))
        self.partner_b2b = self.env['res.partner'].create(dict(
            name="Test Partner B2B",
            vat="BE0477472701",
        ))

    def _configure_accounting(self):
        self.product = self.env['product.product'].create(dict(
            name='product name',
        ))
        self.account_type1 = self.env['account.account.type'].create(dict(
            name='acc type test 1',
            type='receivable',
        ))
        self.account_type2 = self.env['account.account.type'].create(dict(
            name='acc type test 2',
            type='other',
        ))
        self.account_account = self.env['account.account'].create(dict(
            name='acc test',
            code='X2020',
            user_type_id=self.account_type1.id,
            reconcile=True,
        ))
        self.account_account_line = self.env['account.account'].create(dict(
            name='acc inv line test',
            code='X2021',
            user_type_id=self.account_type2.id,
            reconcile=True,
        ))
        self.sale_sequence = self.env['ir.sequence'].create(dict(
            name='Journal Sale',
            prefix='SALE',
            padding=6,
            company_id=self.env.ref("base.main_company").id,
        ))
        self.account_journal_sale = self.env['account.journal'].create(dict(
            name='Sale journal',
            code='SALE',
            type='sale',
            sequence_id=self.sale_sequence.id
        ))

    def create_out_invoice(self, partner):
        invoice = self.env['account.invoice'].create(dict(
            partner_id=partner.id,
            account_id=self.account_account.id,
            type='out_invoice',
            journal_id=self.account_journal_sale.id,
        ))

        self.env['account.invoice.line'].create(dict(
            product_id=self.product.id,
            quantity=1.0,
            price_unit=100.0,
            invoice_id=invoice.id,
            name='product that cost 100',
            account_id=self.account_account_line.id,
        ))
        return invoice

    def test_fiscal_position_vat_check(self):
        # Empty fiscal position should not return a warning
        result = self.partner_b2c.onchange_fiscal_position()
        self.assertEqual(result, None)
        # B2C fiscal position should not return a warning
        self.partner_b2c.property_account_position_id = self.fp_b2c
        result = self.partner_b2c.onchange_fiscal_position()
        self.assertEqual(result, None)
        # B2B fiscal position should return a warning
        self.partner_b2c.property_account_position_id = self.fp_b2b
        result = self.partner_b2c.onchange_fiscal_position()
        self.assertEqual(result['warning']['title'], 'Missing VAT number:')

        # Create Invoice for B2C partner with B2C fiscal position
        self.partner_b2c.property_account_position_id = self.fp_b2c
        invoice = self.create_out_invoice(partner=self.partner_b2c)
        invoice.action_invoice_open()

        # Create Invoice for B2C partner with B2B fiscal position
        self.partner_b2c.property_account_position_id = self.fp_b2b
        invoice = self.create_out_invoice(partner=self.partner_b2c)
        err_msg = "But the Customer '.*' doesn't have a VAT number"
        with self.assertRaisesRegex(UserError, err_msg):
            invoice.action_invoice_open()

        # Empty fiscal position should not return a warning
        result = self.partner_b2b.onchange_fiscal_position()
        self.assertEqual(result, None)
        # B2C fiscal position should not return a warning
        self.partner_b2b.property_account_position_id = self.fp_b2c
        result = self.partner_b2b.onchange_fiscal_position()
        self.assertEqual(result, None)
        # B2B fiscal position should return a warning
        self.partner_b2b.property_account_position_id = self.fp_b2b
        result = self.partner_b2b.onchange_fiscal_position()
        self.assertEqual(result, None)

        # Create Invoice for B2B partner with B2B fiscal position
        self.partner_b2b.property_account_position_id = self.fp_b2b
        invoice = self.create_out_invoice(partner=self.partner_b2b)
        invoice.action_invoice_open()

        # Create Invoice for B2B partner with B2C fiscal position
        self.partner_b2b.property_account_position_id = self.fp_b2c
        invoice = self.create_out_invoice(partner=self.partner_b2b)
        invoice.action_invoice_open()
