# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math

from odoo import models, api, fields, _

import logging
_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _compute_amount_fix(self, base_amount, price_unit, quantity=1.0, product=None, partner=None, force_price_include=False):
        """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
            price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
        """
        self.ensure_one()
        if self.amount_type == 'fixed':
            # Use copysign to take into account the sign of the base amount which includes the sign
            # of the quantity and the sign of the price_unit
            # Amount is the fixed price for the tax, it can be negative
            # Base amount included the sign of the quantity and the sign of the unit price and when
            # a product is returned, it can be done either by changing the sign of quantity or by changing the
            # sign of the price unit.
            # When the price unit is equal to 0, the sign of the quantity is absorbed in base_amount then
            # a "else" case is needed.
            if base_amount:
                return math.copysign(quantity, base_amount) * self.amount
            else:
                return quantity * self.amount
        if self.amount_type == 'percent' and force_price_include:
            return base_amount - (base_amount / (1 + self.amount / 100))
        if (self.amount_type == 'percent' and not self.price_include) or (self.amount_type == 'division' and self.price_include):
            return base_amount * self.amount / 100
        if self.amount_type == 'percent' and self.price_include:
            return base_amount - (base_amount / (1 + self.amount / 100))
        if self.amount_type == 'division' and not self.price_include:
            return base_amount / (1 - self.amount / 100) - base_amount

    def _compute_amount_purchase(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        """ Returns the amount of a single tax. base_amount is the actual amount on which the tax is applied, which is
            price_unit * quantity eventually affected by previous taxes (if tax is include_base_amount XOR price_include)
        """
        self.ensure_one()
        if self.amount_type == 'fixed':
            # Use copysign to take into account the sign of the base amount which includes the sign
            # of the quantity and the sign of the price_unit
            # Amount is the fixed price for the tax, it can be negative
            # Base amount included the sign of the quantity and the sign of the unit price and when
            # a product is returned, it can be done either by changing the sign of quantity or by changing the
            # sign of the price unit.
            # When the price unit is equal to 0, the sign of the quantity is absorbed in base_amount then
            # a "else" case is needed.
            if base_amount:
                return math.copysign(quantity, base_amount) * self.amount
            else:
                return quantity * self.amount
        if self.tax_credit_payable == 'taxadvpay':
            base_amount = 0.0
        if (self.amount_type == 'percent' and not self.price_include) or (self.amount_type == 'division' and self.price_include):
            return base_amount * self.amount / 100
        if self.amount_type == 'percent' and self.price_include:
            return base_amount - (base_amount / (1 + self.amount / 100))
        if self.amount_type == 'division' and not self.price_include:
            return base_amount / (1 - self.amount / 100) - base_amount

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        if self._context.get('force_fix', False):
            ret = self._compute_amount_fix(base_amount, price_unit, quantity=quantity, product=product, partner=partner, force_price_include=True)
        elif self._context.get('force_purchase', False):
            ret = self._compute_amount_purchase(base_amount, price_unit, quantity=quantity, product=product, partner=partner)
        else:
            ret = super(AccountTax, self)._compute_amount(base_amount, price_unit, quantity=quantity, product=product, partner=partner)
        return ret

    @api.multi
    def compute_all(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        if self._context.get('force_fix', False):
            return self.compute_all_fix(price_unit, currency=currency, quantity=quantity, product=product, partner=partner, force_price_include=True)
        if self._context.get('comapany_currency', False):
            return self.compute_all_currency(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)
        if self._context.get('customs_fix'):
            tax = self.compute_all_customs_fix(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)
            if tax:
                return tax
        return super(AccountTax, self).compute_all(price_unit, currency=currency, quantity=quantity, product=product, partner=partner)

    @api.multi
    def compute_all_currency(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        taxes_base = {}
        taxes = super(AccountTax, self).compute_all(price_unit, currency=currency, quantity=quantity, product=product,
                                                    partner=partner)
        for tax in taxes:
            taxes_base[tax['id']] = tax
        taxes_currency = super(AccountTax, self).compute_all(price_unit, currency=company_id.currency_id, quantity=quantity,
                                                             product=product, partner=partner)
        for tax in taxes_currency:
            tax.update({
                'amount_currency': tax['amount'],
                'base_currency': tax['base'],
                'amount': taxes_base[tax['id']]['amount'],
                'base': taxes_base[tax['id']]['base'],
            })
        return taxes_currency

    @api.multi
    def compute_all_customs_fix(self, price_unit, currency=None, quantity=1.0, product=None, partner=None):
        return {}

    @api.multi
    def compute_all_fix(self, price_unit, currency=None, quantity=1.0, product=None, partner=None, force_price_include=False):
        """ Returns all information required to apply taxes (in self + their children in case of a tax goup).
            We consider the sequence of the parent for group of taxes.
                Eg. considering letters as taxes and alphabetic order as sequence :
                [G, B([A, D, F]), E, C] will be computed as [A, D, F, C, E, G]

        RETURN: {
            'total_excluded': 0.0,    # Total without taxes
            'total_included': 0.0,    # Total with taxes
            'taxes': [{               # One dict for each tax in self and their children
                'id': int,
                'name': str,
                'amount': float,
                'sequence': int,
                'account_id': int,
                'refund_account_id': int,
                'analytic': boolean,
            }]
        } """
        if len(self) == 0:
            company_id = self.env.user.company_id
        else:
            company_id = self[0].company_id
        if not currency:
            currency = company_id.currency_id
        taxes = []
        # By default, for each tax, tax amount will first be computed
        # and rounded at the 'Account' decimal precision for each
        # PO/SO/invoice line and then these rounded amounts will be
        # summed, leading to the total amount for that tax. But, if the
        # company has tax_calculation_rounding_method = round_globally,
        # we still follow the same method, but we use a much larger
        # precision when we round the tax amount for each line (we use
        # the 'Account' decimal precision + 5), and that way it's like
        # rounding after the sum of the tax amounts of each line
        prec = currency.decimal_places

        # In some cases, it is necessary to force/prevent the rounding of the tax and the total
        # amounts. For example, in SO/PO line, we don't want to round the price unit at the
        # precision of the currency.
        # The context key 'round' allows to force the standard behavior.
        round_tax = False if company_id.tax_calculation_rounding_method == 'round_globally' else True
        round_total = True
        if 'round' in self.env.context:
            round_tax = bool(self.env.context['round'])
            round_total = bool(self.env.context['round'])

        if not round_tax:
            prec += 5

        base_values = self.env.context.get('base_values')
        if not base_values:
            total_excluded = total_included = base = round(price_unit * quantity, prec)
        else:
            total_excluded, total_included, base = base_values

        # Sorting key is mandatory in this case. When no key is provided, sorted() will perform a
        # search. However, the search method is overridden in account.tax in order to add a domain
        # depending on the context. This domain might filter out some taxes from self, e.g. in the
        # case of group taxes.
        for tax in self.sorted(key=lambda r: r.sequence):
            if tax.amount_type == 'group':
                children = tax.children_tax_ids.with_context(base_values=(total_excluded, total_included, base))
                ret = children.compute_all(price_unit, currency, quantity, product, partner)
                total_excluded = ret['total_excluded']
                base = ret['base'] if tax.include_base_amount else base
                total_included = ret['total_included']
                tax_amount = total_included - total_excluded
                taxes += ret['taxes']
                continue

            tax_amount = tax._compute_amount(base, price_unit, quantity, product, partner)
            if not round_tax:
                tax_amount = round(tax_amount, prec)
            else:
                tax_amount = currency.round(tax_amount)

            if tax.price_include or force_price_include:
                total_excluded -= tax_amount
                base -= tax_amount
            else:
                total_included += tax_amount

            # Keep base amount used for the current tax
            tax_base = base

            if tax.include_base_amount:
                base += tax_amount

            taxes.append({
                'id': tax.id,
                'name': tax.with_context(**{'lang': partner.lang} if partner else {}).name,
                'amount': tax_amount,
                'base': tax_base,
                'sequence': tax.sequence,
                'account_id': tax.account_id.id,
                'refund_account_id': tax.refund_account_id.id,
                'analytic': tax.analytic,
                'price_include': tax.price_include,
            })

        return {
            'taxes': sorted(taxes, key=lambda k: k['sequence']),
            'total_excluded': currency.round(total_excluded) if round_total else total_excluded,
            'total_included': currency.round(total_included) if round_total else total_included,
            'base': base,
        }

    @api.multi
    def json_friendly_compute_all_fix(self, price_unit, currency_id=None, quantity=1.0, product_id=None, partner_id=None):
        """ Just converts parameters in browse records and calls for compute_all, because js widgets can't serialize browse records """
        if currency_id:
            currency_id = self.env['res.currency'].browse(currency_id)
        if product_id:
            product_id = self.env['product.product'].browse(product_id)
        if partner_id:
            partner_id = self.env['res.partner'].browse(partner_id)
        return self.with_context(self._context, force_fix=True).compute_all(price_unit, currency=currency_id, quantity=quantity, product=product_id, partner=partner_id)
