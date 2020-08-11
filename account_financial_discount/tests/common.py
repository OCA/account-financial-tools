# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.tests.common import Form, SavepointCase


class TestAccountFinancialDiscountCommon(SavepointCase):
    @classmethod
    def init_invoice(
        cls,
        partner,
        move_type,
        payment_term=None,
        invoice_date=None,
        invoice_date_due=None,
        currency=None,
    ):
        move_form = Form(
            cls.env['account.move'].with_context(default_type=move_type)
        )
        move_form.partner_id = partner
        move_form.invoice_payment_term_id = payment_term
        move_form.invoice_date = invoice_date
        move_form.invoice_date_due = invoice_date_due
        if currency is not None:
            move_form.currency_id = currency
        return move_form.save()

    @classmethod
    def init_invoice_line(
        cls, invoice, quantity, unit_price, product=None, with_tax=True
    ):
        with Form(invoice) as move_form:
            with move_form.invoice_line_ids.new() as line_form:
                if product:
                    line_form.product_id = product
                line_form.name = product and product.name or 'test'
                line_form.quantity = quantity
                line_form.price_unit = unit_price
                if not with_tax:
                    line_form.tax_ids.clear()

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create(
            {'name': 'Peter Muster AG', 'supplier_rank': 1}
        )
        cls.customer = cls.env['res.partner'].create(
            {'name': 'Hans Muster GmbH & Co. KG', 'customer_rank': 1}
        )

        cls.write_off_rev = cls.env['account.account'].create(
            {
                'code': 'wrtrev',
                'name': 'writeoff revenue',
                'user_type_id': cls.env.ref(
                    'account.data_account_type_expenses'
                ).id,
                'reconcile': False,
            }
        )
        cls.write_off_exp = cls.env['account.account'].create(
            {
                'code': 'wrtexp',
                'name': 'writeoff expenses',
                'user_type_id': cls.env.ref(
                    'account.data_account_type_expenses'
                ).id,
                'reconcile': False,
            }
        )
        cls.env.company.financial_discount_expense_account_id = (
            cls.write_off_exp
        )
        cls.env.company.financial_discount_revenue_account_id = (
            cls.write_off_rev
        )
        cls.payment_term = cls.env['account.payment.term'].create(
            {
                'name': 'Skonto',
                'days_discount': 10,
                'percent_discount': 2.0,
                'line_ids': [
                    (
                        0,
                        0,
                        {
                            'value': 'balance',
                            'days': 60,
                            'option': 'day_after_invoice_date',
                        },
                    )
                ],
            }
        )
        cls.payable_account = cls.env['account.account'].search(
            [('user_type_id.name', '=', 'Payable')], limit=1
        )
        cls.receivable_account = cls.env['account.account'].search(
            [('user_type_id.name', '=', 'Receivable')], limit=1
        )
        cls.bank_journal = cls.env['account.journal'].search(
            [('company_id', '=', cls.env.company.id), ('type', '=', 'bank')],
            limit=1,
        )

        cls.exp = cls.env['account.account'].create(
            {
                'code': 'exp',
                'name': 'expenses',
                'user_type_id': cls.env.ref(
                    'account.data_account_type_expenses'
                ).id,
                'reconcile': True,
            }
        )

        cls.payment_thirty_net = cls.env.ref(
            'account.account_payment_term_30days'
        )

        cls.payment_method_manual_out = cls.env.ref(
            "account.account_payment_method_manual_out"
        )

        cls.usd_currency = cls.env.ref("base.USD")
        cls.eur_currency = cls.env.ref("base.EUR")
