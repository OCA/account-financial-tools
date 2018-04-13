# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil.relativedelta import relativedelta
import logging
import math

_logger = logging.getLogger(__name__)
try:
    import numpy
except (ImportError, IOError) as err:
    _logger.error(err)


class AccountLoan(models.Model):
    _name = 'account.loan'
    _description = 'Loan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def _default_company(self):
        force_company = self._context.get('force_company')
        if not force_company:
            return self.env.user.company_id.id
        return force_company

    name = fields.Char(
        copy=False,
        required=True,
        readonly=True,
        default='/',
        states={'draft': [('readonly', False)]},
    )
    partner_id = fields.Many2one(
        'res.partner',
        required=True,
        string='Lender',
        help='Company or individual that lends the money at an interest rate.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=_default_company,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ], required=True, copy=False, default='draft')
    line_ids = fields.One2many(
        'account.loan.line',
        readonly=True,
        inverse_name='loan_id',
        copy=False,
    )
    periods = fields.Integer(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Number of periods that the loan will last',
    )
    method_period = fields.Integer(
        string='Period Length',
        default=1,
        help="State here the time between 2 depreciations, in months",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    start_date = fields.Date(
        help='Start of the moves',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
    )
    rate = fields.Float(
        required=True,
        default=0.0,
        digits=(8, 6),
        help='Currently applied rate',
        track_visibility='always',
    )
    rate_period = fields.Float(
        compute='_compute_rate_period', digits=(8, 6),
        help='Real rate that will be applied on each period',
    )
    rate_type = fields.Selection(
        [
            ('napr', 'Nominal APR'),
            ('ear', 'EAR'),
            ('real', 'Real rate'),
        ],
        required=True,
        help='Method of computation of the applied rate',
        default='napr',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    loan_type = fields.Selection(
        [
            ('fixed-annuity', 'Fixed Annuity'),
            ('fixed-principal', 'Fixed Principal'),
            ('interest', 'Only interest'),
        ],
        required=True,
        help='Method of computation of the period annuity',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default='fixed-annuity'
    )
    fixed_amount = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_fixed_amount',
    )
    fixed_loan_amount = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        copy=False,
        default=0,
    )
    fixed_periods = fields.Integer(
        readonly=True,
        copy=False,
        default=0,
    )
    loan_amount = fields.Monetary(
        currency_field='currency_id',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    residual_amount = fields.Monetary(
        currency_field='currency_id',
        default=0.,
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='Residual amount of the lease that must be payed on the end in '
             'order to acquire the asset',
    )
    round_on_end = fields.Boolean(
        default=False,
        help='When checked, the differences will be applied on the last period'
             ', if it is unchecked, the annuity will be recalculated on each '
             'period.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    payment_on_first_period = fields.Boolean(
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='When checked, the first payment will be on start date',
    )
    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_currency',
        readonly=True,
    )
    journal_type = fields.Char(compute='_compute_journal_type')
    journal_id = fields.Many2one(
        'account.journal',
        domain="[('company_id', '=', company_id),('type', '=', journal_type)]",
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    short_term_loan_account_id = fields.Many2one(
        'account.account',
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
        string='Short term account',
        help='Account that will contain the pending amount on short term',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    long_term_loan_account_id = fields.Many2one(
        'account.account',
        string='Long term account',
        help='Account that will contain the pending amount on Long term',
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    interest_expenses_account_id = fields.Many2one(
        'account.account',
        domain="[('company_id', '=', company_id), ('deprecated', '=', False)]",
        string='Interests account',
        help='Account where the interests will be assigned to',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    is_leasing = fields.Boolean(
        default=False,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    leased_asset_account_id = fields.Many2one(
        'account.account',
        domain="[('company_id', '=', company_id)]",
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    product_id = fields.Many2one(
        'product.product',
        string='Loan product',
        help='Product where the amount of the loan will be assigned when the '
             'invoice is created',
    )
    interests_product_id = fields.Many2one(
        'product.product',
        string='Interest product',
        help='Product where the amount of interests will be assigned when the '
             'invoice is created',
    )
    move_ids = fields.One2many(
        'account.move',
        copy=False,
        inverse_name='loan_id'
    )
    pending_principal_amount = fields.Monetary(
        currency_field='currency_id',
        compute='_compute_total_amounts',
    )
    payment_amount = fields.Monetary(
        currency_field='currency_id',
        string='Total payed amount',
        compute='_compute_total_amounts',
    )
    interests_amount = fields.Monetary(
        currency_field='currency_id',
        string='Total interests payed',
        compute='_compute_total_amounts',
    )

    description = fields.Char(string='Description', index=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name, company_id)',
         'Loan name must be unique'),
    ]

    @api.depends('line_ids', 'currency_id', 'loan_amount')
    def _compute_total_amounts(self):
        for record in self:
            lines = record.line_ids.filtered(lambda r: r.move_ids)
            record.payment_amount = sum(
                lines.mapped('payment_amount')) or 0.
            record.interests_amount = sum(
                lines.mapped('interests_amount')) or 0.
            record.pending_principal_amount = (
                record.loan_amount -
                record.payment_amount +
                record.interests_amount
            )

    @api.depends('rate_period', 'fixed_loan_amount', 'fixed_periods',
                 'currency_id')
    def _compute_fixed_amount(self):
        """
        Computes the fixed amount in order to be used if round_on_end is
        checked. On fix-annuity interests are included and on fixed-principal
        and interests it isn't.
        :return:
        """
        for record in self:
            if record.loan_type == 'fixed-annuity':
                record.fixed_amount = - record.currency_id.round(numpy.pmt(
                    record.rate_period / 100,
                    record.fixed_periods,
                    record.fixed_loan_amount,
                    -record.residual_amount
                ))
            elif record.loan_type == 'fixed-principal':
                record.fixed_amount = record.currency_id.round(
                    (record.fixed_loan_amount - record.residual_amount) /
                    record.fixed_periods
                )
            else:
                record.fixed_amount = 0.0

    @api.model
    def compute_rate(self, rate, rate_type, method_period):
        """
        Returns the real rate
        :param rate: Rate
        :param rate_type: Computation rate
        :param method_period: Number of months between payments
        :return:
        """
        if rate_type == 'napr':
            return rate / 12 * method_period
        if rate_type == 'ear':
            return math.pow(1 + rate, method_period / 12) - 1
        return rate

    @api.depends('rate', 'method_period', 'rate_type')
    def _compute_rate_period(self):
        for record in self:
            record.rate_period = record.compute_rate(
                record.rate, record.rate_type, record.method_period)

    @api.depends('journal_id', 'company_id')
    def _compute_currency(self):
        for rec in self:
            rec.currency_id = (
                rec.journal_id.currency_id or rec.company_id.currency_id)

    @api.depends('is_leasing')
    def _compute_journal_type(self):
        for record in self:
            if record.is_leasing:
                record.journal_type = 'purchase'
            else:
                record.journal_type = 'general'

    @api.onchange('is_leasing')
    def _onchange_is_leasing(self):
        self.journal_id = self.env['account.journal'].search([
            ('company_id', '=', self.company_id.id),
            ('type', '=', 'purchase' if self.is_leasing else 'general')
        ], limit=1)
        self.residual_amount = 0.0

    @api.onchange('company_id')
    def _onchange_company(self):
        self._onchange_is_leasing()
        self.interest_expenses_account_id = False
        self.short_term_loan_account_id = False
        self.long_term_loan_account_id = False

    def get_default_name(self, vals):
        return self.env['ir.sequence'].next_by_code('account.loan') or '/'

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.get_default_name(vals)
        return super().create(vals)

    @api.multi
    def post(self):
        self.ensure_one()
        if not self.start_date:
            self.start_date = fields.Datetime.now()
        self.compute_draft_lines()
        msg_values = {
            _('Lender'): self.partner_id.name,
            _('Periods'): self.periods,
            _('Period Length'): self.method_period,
            _('Start Date'): self.start_date,
            _('Rate'): self.rate,
            _('Rate Period'): self.rate_period,
            _('Rate Type'): self.rate_type,
            _('Loan Type'): self.loan_type,
            _('Currency'): self.currency_id.name,
            _('Loan Amount'): self.loan_amount,
            }
        msg = self._format_message(_("Loan posted."), msg_values)
        self.message_post(body=msg)
        self.write({'state': 'posted'})

    @api.multi
    def close(self):
        payment_amount = 0
        interests_amount = 0
        principal_amount = 0
        for line in self.line_ids:
            payment_amount += line.payment_amount
            interests_amount += line.interests_amount
            principal_amount += line.principal_amount
            if line.sequence == self.periods:
                line.log_posted_line()
        pending_principal_amount = self.loan_amount - payment_amount + interests_amount
        msg_values = {
            _('End Date'): datetime.now().date(),
            _('Total Pending Principal Amount'): pending_principal_amount,
            _('Total Payment Amount'): payment_amount,
            _('Total Interests Amount'): interests_amount,
            _('Total Principal Amount'): principal_amount,
            }
        msg = self._format_message(_("Loan closed."), msg_values)
        self.message_post(body=msg)
        self.write({'state': 'closed'})

    @api.multi
    def compute_lines(self):
        self.ensure_one()
        if self.state == 'draft':
            return self.compute_draft_lines()
        return self.compute_posted_lines()

    def compute_posted_lines(self):
        """
        Recompute the amounts of not finished lines. Useful if rate is changed
        """
        amount = self.loan_amount
        for line in self.line_ids.sorted('sequence'):
            if line.move_ids:
                amount = line.final_pending_principal_amount
            else:
                line.rate = self.rate_period
                line.pending_principal_amount = amount
                line.check_amount()
                amount -= line.payment_amount - line.interests_amount
        if self.long_term_loan_account_id:
            self.check_long_term_principal_amount()

    def check_long_term_principal_amount(self):
        """
        Recomputes the long term pending principal of unfinished lines.
        """
        lines = self.line_ids.filtered(lambda r: not r.move_ids)
        amount = 0
        final_sequence = min(lines.mapped('sequence'))
        for line in lines.sorted('sequence', reverse=True):
            date = datetime.strptime(
                line.date, DF).date() + relativedelta(months=12)
            if self.state == 'draft' or line.sequence != final_sequence:
                line.long_term_pending_principal_amount = sum(
                    self.line_ids.filtered(
                        lambda r: datetime.strptime(r.date, DF).date() >= date
                    ).mapped('principal_amount'))
            line.long_term_principal_amount = (
                line.long_term_pending_principal_amount - amount)
            amount = line.long_term_pending_principal_amount

    def new_line_vals(self, sequence, date, amount):
        return {
            'loan_id': self.id,
            'sequence': sequence,
            'date': date,
            'pending_principal_amount': amount,
            'rate': self.rate_period,
        }

    @api.multi
    def compute_draft_lines(self):
        self.ensure_one()
        self.fixed_periods = self.periods
        self.fixed_loan_amount = self.loan_amount
        self.line_ids.unlink()
        amount = self.loan_amount
        if self.start_date:
            date = datetime.strptime(self.start_date, DF).date()
        else:
            date = datetime.today().date()
        delta = relativedelta(months=self.method_period)
        if not self.payment_on_first_period:
            date += delta
        for i in range(1, self.periods + 1):
            line = self.env['account.loan.line'].create(
                self.new_line_vals(i, date, amount)
            )
            line.check_amount()
            date += delta
            amount -= line.payment_amount - line.interests_amount
        if self.long_term_loan_account_id:
            self.check_long_term_principal_amount()

    @api.multi
    def view_account_moves(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_line_form')
        result = action.read()[0]
        result['domain'] = [('loan_id', '=', self.id)]
        return result

    @api.multi
    def view_account_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]
        result['domain'] = [
            ('loan_id', '=', self.id),
            ('type', '=', 'in_invoice')
        ]
        return result

    @api.model
    def generate_loan_entries(self, date):
        """
        Generate the moves of unfinished loans before date
        :param date:
        :return:
        """
        res = []
        for record in self.search([
            ('state', '=', 'posted'),
            ('is_leasing', '=', False)
        ]):
            lines = record.line_ids.filtered(
                lambda r: datetime.strptime(
                    r.date, DF).date() <= date and not r.move_ids
            )
            res += lines.generate_move()
        return res

    @api.model
    def generate_leasing_entries(self, date):
        res = []
        for record in self.search([
            ('state', '=', 'posted'),
            ('is_leasing', '=', True)
        ]):
            res += record.line_ids.filtered(
                lambda r: datetime.strptime(
                    r.date, DF).date() <= date and not r.invoice_ids
            ).generate_invoice()
        return res
	
    def _format_message(self, msg_description=None, msg_values=None):
        msg = ''
        if msg_description:
            msg = '<strong>%s</strong>' % msg_description
        if msg_values:
            for name, value in msg_values.items():
                msg += '<div>- <strong>%s</strong>: ' % name
                msg += '%s</div>' % value
        return msg