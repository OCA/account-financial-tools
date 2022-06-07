# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
from odoo.tools import float_compare
from odoo.exceptions import ValidationError, UserError


class AccountPaymentIntransit(models.Model):
    _inherit = 'account.payment.intransit'

    total_amount = fields.Monetary(
        string='Total',
        compute='_compute_payment_intransit',
        copy=False,
    )
    manual_total_amount = fields.Monetary(
        string="Total Amount",
        default=0.0,
        readonly=True,
        states={'draft': [('readonly', False)]},
        required=True,
    )
    payment_difference = fields.Monetary(
        compute='_compute_payment_difference',
        readonly=True
    )
    deduction_ids = fields.One2many(
        comodel_name='account.payment.intransit.deduction',
        inverse_name='payment_intransit_id',
        string='Deductions',
        copy=False,
        states={'done': [('readonly', '=', True)]},
        help="Sum of deduction amount(s) must equal to the payment difference",
    )

    @api.model
    def _prepare_writeoff_move_line(self, move, rate_currency=None):
        move_line_dict = []
        for writeoffline in self.deduction_ids:
            if rate_currency:
                move_line_dict.append({
                    'name': _('Payment Diff - %s') % writeoffline.name,
                    'credit': 0.0,
                    'debit': writeoffline.amount/rate_currency,
                    'account_id': writeoffline.account_id.id,
                    'currency_id': writeoffline.currency_id.id or False,
                    'amount_currency': writeoffline.amount,
                    'move_id': move.id,
                })
            else:
                move_line_dict.append({
                    'name': _('Payment Diff - %s') % writeoffline.name,
                    'credit': 0.0,
                    'debit': writeoffline.amount,
                    'account_id': writeoffline.account_id.id,
                    'move_id': move.id,
                })
        return move_line_dict

    @api.model
    def _create_writeoff_move_line_hook(self, move, rate_currency=None):
        super(AccountPaymentIntransit, self)._create_writeoff_move_line_hook(
            move)
        move_line_obj = self.env['account.move.line']
        move_line_val = self._prepare_writeoff_move_line(move, rate_currency)
        move_line_obj.with_context(
            check_move_validity=False).create(move_line_val)
        return True

    @api.multi
    @api.depends('manual_total_amount')
    def _compute_payment_intransit(self):
        res = super(AccountPaymentIntransit, self)._compute_payment_intransit()
        for payment in self:
            payment.total_amount = payment.manual_total_amount
        return res

    @api.multi
    def validate_payment_intransit(self):
        for rec in self:
            if rec.payment_difference and not rec.deduction_ids:
                raise ValidationError(_('No lines in Payment Difference.'))
        res = super(AccountPaymentIntransit, self).validate_payment_intransit()
        return res

    @api.one
    @api.constrains('total_amount')
    def _check_amount(self):
        if self.total_amount < 0:
            raise ValidationError(_(
                'The payment intransit amount cannot be negative.'))

    @api.one
    @api.constrains('deduction_ids')
    def _check_deduct_residual(self):
        prec_digits = self.env.user.company_id.currency_id.decimal_places
        if float_compare(self.payment_difference,
                         sum(self.deduction_ids.mapped('amount')),
                         precision_digits=prec_digits) != 0:
            raise UserError(_('The total deduction should be %s') %
                            self.payment_difference)

    @api.depends('total_amount')
    def _compute_payment_difference(self):
        allocation = sum(self.intransit_line_ids.mapped('allocation'))
        self.payment_difference = allocation - self.total_amount
