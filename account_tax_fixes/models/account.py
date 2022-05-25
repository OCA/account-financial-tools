# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import math

from odoo import models, api, fields, _

import logging

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountTax(models.Model):
    _inherit = 'account.tax'

    def _get_tax_credit_payable(self):
        return self.env['account.tax.template']._get_tax_credit_payable()

    tax_credit_payable = fields.Selection(selection='_get_tax_credit_payable', string='Who pays tax', required=False,
                                          default='taxpay',
                                          help="If not applicable (computed through a Python code), the tax won't "
                                               "appear on the invoice.Who pays the tax purchaser or seller ( for "
                                               "imports from outside the EU pay the buyer )")

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
            return 0.0
        if (self.amount_type == 'percent' and not self.price_include) or (self.amount_type == 'division' and self.price_include):
            return base_amount * self.amount / 100
        if self.amount_type == 'percent' and self.price_include:
            return base_amount - (base_amount / (1 + self.amount / 100))
        if self.amount_type == 'division' and not self.price_include:
            return base_amount / (1 - self.amount / 100) - base_amount

    def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
        if self._context.get('force_fix', False):
            ret = self._compute_amount_fix(base_amount, price_unit, quantity=quantity, product=product, partner=partner, force_price_include=True)
        elif self._context.get('force_purchase', False) or self._name == 'purchase.order.line':
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


class AccountAccountTag(models.Model):
    _inherit = 'account.account.tag'
    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'name'
    _order = 'parent_left'

    def _get_type_taxes(self):
        return self.env['account.account.tag.template']._get_type_taxes()

    def _get_type_info(self):
        return self.env['account.account.tag.template']._get_type_info()

    code = fields.Char("Code", index=True, copy=False)
    account_ids = fields.Many2many('account.account', relation='account_account_account_tag',
                                   column1='account_account_tag_id', column2='account_account_id', string='Accounts',
                                   help="Assigned accounts for custom reporting")
    tax_ids = fields.Many2many('account.tax', 'account_tax_account_tag',
                               column1='account_account_tag_id', column2='account_tax_id', string='Taxes',
                               help="Assigned taxes for custom reporting")

    color_picker = fields.Selection([('0', 'Grey'),
                                     ('1', 'Green'),
                                     ('2', 'Yellow'),
                                     ('3', 'Orange'),
                                     ('4', 'Red'),
                                     ('5', 'Purple'),
                                     ('6', 'Blue'),
                                     ('7', 'Cyan'),
                                     ('8', 'Aquamarine'),
                                     ('9', 'Pink')], string='Tags Color',
                                    required=True, default='0')
    color = fields.Integer('Color Index', compute='_compute_color_index', store=True)

    parent_id = fields.Many2one('account.account.tag', string='Parent Tag', index=True, ondelete='cascade')
    child_ids = fields.One2many('account.account.tag', 'parent_id', string='Child Tags')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env['res.company']._company_default_get(
                                     'account.account.tag'))

    type_taxes = fields.Selection(selection='_get_type_taxes', string='Type taxes')
    type_info = fields.Selection(selection='_get_type_info', string='Type info')

    display_name = fields.Char(compute='_compute_display_name')

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for tag in self:
            if self._context.get('only_code'):
                tag.display_name = "%s" % tag.code
            if tag.code and tag.name:
                tag.display_name = "[%s] %s" % (tag.code, tag.name)
            elif tag.code and not tag.name:
                tag.display_name = "%s" % tag.code
            elif tag.name and not tag.code:
                tag.display_name = "%s" % tag.code
            else:
                tag.display_name = "%s" % tag.code

    @api.depends('color_picker')
    def _compute_color_index(self):
        for tag in self:
            if tag.parent_id:
                color = tag.parent_id.color_picker
            else:
                color = tag.color_picker
            tag.color = int(color)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You can not create recursive tags.'))

    @api.model
    def name_create(self, name):
        return self.create({'name': name}).name_get()[0]

    @api.multi
    def name_get(self):
        """ Return the tags' display name, including their direct
            parent by default.

            If ``context['account_tag_display']`` is ``'short'``, the short
            version of the category name (without the direct parent) is used.
            The default is the long version.
        """
        if self._context.get('account_tag_display') == 'short':
            return super(AccountAccountTag, self).name_get()

        res = []
        for tag in self:
            names = []
            current = tag
            while current:
                names.append("[%s] %s" % (current.code, current.name))
                current = current.parent_id
            res.append((tag.id, ' / '.join(reversed(names))))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            # Be sure name_search is symetric to name_get
            name = name.split(' / ')[-1]
            args = [('name', operator, name)] + args
        return self.search(args, limit=limit).name_get()
