# -*- coding: utf-8 -*-
from decimal import Decimal, ROUND_UP, getcontext
from openerp import models, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.one
    def update_debit_credit(self):
        currency = self.currency_id
        if currency:
            amount_currency = self.amount_currency
            company_currency = self.env.user.company_id.currency_id
            # False is for not rounding the result of the conversion
            converted_amount = abs(currency.with_context(
                date=self.move_id.date
            ).compute(amount_currency, company_currency, False))
            getcontext().prec = 12
            converted_amount = "{0:.2f}".format(
                Decimal(converted_amount).quantize(Decimal('.01'),
                                                   rounding=ROUND_UP)
            )
            self.debit = converted_amount if amount_currency > 0 else 0.0
            self.credit = converted_amount if amount_currency < 0 else 0.0

    @api.cr_uid_context
    def create(self, cr, uid, vals, context=None, check=True):
        record_id = super(AccountMoveLine, self).create(
            cr, uid, vals, context=context, check=check
        )
        if vals.get('amount_currency'):
            # if it has not been converted yet
            if not (vals.get('credit') or vals.get('debit')):
                self.update_debit_credit(cr, uid, [record_id], context=context)
        return record_id

    @api.cr_uid_ids_context
    def write(self, cr, uid, ids, vals, context=None, check=True,
              update_check=True):
        result = super(AccountMoveLine, self).write(
            cr, uid, ids, vals, context=context,
            check=check, update_check=update_check
        )
        if ('currency_id' in vals) or ('amount_currency' in vals):
            # if it has not been converted yet
            if not (vals.get('credit') or vals.get('debit')):
                self.update_debit_credit(cr, uid, ids, context=context)
        return result

    @api.onchange('currency_id', 'amount_currency')
    @api.model
    def _onchange_currency(self):
        self.update_debit_credit()
