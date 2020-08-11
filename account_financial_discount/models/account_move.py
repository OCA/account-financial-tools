# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    has_discount_available = fields.Boolean(
        'Has discount available',
        compute='_compute_financial_discount_data',
        # TODO implement read_group + search because we cannot store the field
        #  as it depends on actual date
    )
    display_force_financial_discount = fields.Boolean(
        compute='_compute_financial_discount_data'
    )
    force_financial_discount = fields.Boolean(
        'Force financial discount?',
        default=False,
        help="If marked, financial discount will be applied even if the "
        "discount date is passed",
    )
    payment_blocked = fields.Boolean(
        'Is payment blocked',
        default=False,
        help="Allows group-by but has no logic linked to it",
    )

    # TODO refactor the two functions below together
    def _get_discount_available(self):
        self.ensure_one()
        if self.state == 'draft':
            if (
                self.invoice_payment_term_id.days_discount
                and self.invoice_payment_term_id.percent_discount
                and (
                    (
                        not self.invoice_date
                        or date.today()
                        <= self.invoice_payment_term_id.calc_discount_date(
                            self.invoice_date
                        )
                    )
                    or self.force_financial_discount
                )
            ):
                return True
        elif self.state == 'posted':
            disc_date = self._get_first_payment_term_line().date_discount
            if (
                disc_date
                and disc_date >= date.today()
                or self.force_financial_discount
            ):
                return True
        return False

    def _get_display_force_financial_discount(self):
        self.ensure_one()
        if self.state == 'draft':
            if (
                self.invoice_payment_term_id.days_discount
                and self.invoice_payment_term_id.percent_discount
            ):
                return True
        elif self.state == 'posted':
            first_payment_term_line = self._get_first_payment_term_line()
            if (
                first_payment_term_line.date_discount
                and first_payment_term_line.amount_discount
            ):
                return True
        return False

    def _get_discount_amount(self, amount=None):
        self.ensure_one()
        if amount is None:
            amount = self.amount_total
        discount_amount = 0.0
        if self.invoice_payment_term_id.percent_discount:
            discount_amount = amount * (
                self.invoice_payment_term_id.percent_discount / 100
            )
        return discount_amount

    @api.depends(
        'invoice_date',
        'invoice_payment_term_id',
        'invoice_payment_term_id.days_discount',
        'invoice_payment_term_id.percent_discount',
        'force_financial_discount',
    )
    def _compute_financial_discount_data(self):
        """Compute discount financial discount fields"""
        for rec in self:
            rec.has_discount_available = rec._get_discount_available()
            rec.display_force_financial_discount = (
                rec._get_display_force_financial_discount()
            )

    def post(self):
        res = super().post()
        self._store_financial_discount()
        return res

    def _get_first_payment_term_line(self):
        self.ensure_one()
        payment_term_lines = self.line_ids.filtered(
            lambda line: line.account_id.user_type_id.type
            in ('receivable', 'payable')
        )
        return fields.first(payment_term_lines.sorted('date_maturity'))

    def _get_taxes_lines(self):
        self.ensure_one()
        taxes_applied = self.line_ids.mapped('tax_ids')
        taxes_lines = self.line_ids.filtered(
            lambda line: line.tax_line_id in taxes_applied
        )
        return taxes_lines

    def _store_financial_discount(self):
        """Add discount data to payment term lines."""
        for move in self:
            payment_term = move.invoice_payment_term_id
            payment_term_line = move._get_first_payment_term_line()
            tax_line = move._get_taxes_lines()
            # check if we have a discount on the payment term
            if (
                payment_term.days_discount
                and payment_term.percent_discount
                and len(tax_line) <= 1
                and (
                    (move.type == 'out_invoice' and payment_term_line.debit)
                    or (move.type == 'in_invoice' and payment_term_line.credit)
                )
            ):
                pay_term_vals = move._prepare_discount_vals(payment_term)
                if tax_line:
                    tax_discount_amount = move._get_discount_amount(
                        tax_line.debit or tax_line.credit
                    )
                    if move.type == 'in_invoice':
                        tax_discount_amount = -tax_discount_amount
                    pay_term_vals.update(
                        {
                            'discount_tax_line_id': tax_line.id,
                            'amount_discount_tax': tax_discount_amount,
                        }
                    )
                payment_term_line.write(pay_term_vals)

    def _prepare_discount_vals(self, payment_term):
        self.ensure_one()
        vals = dict()
        if not payment_term.days_discount or not payment_term.percent_discount:
            vals.update(
                {
                    'amount_discount': 0,
                    'amount_discount_currency': 0,
                    'date_discount': False,
                }
            )
        else:
            company_currency = self.company_id.currency_id
            diff_currency = self.currency_id != company_currency
            date_invoice = (
                self.date or self.invoice_date or fields.Date.today()
            )
            date_discount = payment_term.calc_discount_date(date_invoice)
            # if there is a discount defined we always want the amount
            # the date is enough to lock it down.
            amount_discount_invoice_currency = self._get_discount_amount()
            vals['date_discount'] = date_discount
            amount_discount_company_currency = False
            if diff_currency:
                amount_discount_company_currency = self.currency_id._convert(
                    amount_discount_invoice_currency,
                    company_currency,
                    self.company_id,
                    date_invoice,
                )
            if self.type == 'out_invoice':
                if diff_currency:
                    vals['amount_discount'] = amount_discount_company_currency
                    vals[
                        'amount_discount_currency'
                    ] = amount_discount_invoice_currency
                else:
                    vals['amount_discount'] = amount_discount_invoice_currency
            elif self.type == 'in_invoice':
                if diff_currency:
                    vals['amount_discount'] = -amount_discount_company_currency
                    vals[
                        'amount_discount_currency'
                    ] = -amount_discount_invoice_currency
                else:
                    vals['amount_discount'] = -amount_discount_invoice_currency
        return vals
