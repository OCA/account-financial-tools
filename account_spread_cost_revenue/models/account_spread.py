# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import calendar
import time

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class AccountSpread(models.Model):
    _name = 'account.spread'
    _description = 'Account Spread'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    template_id = fields.Many2one(
        'account.spread.template',
        string='Spread Template')
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note')],
        required=True)
    spread_type = fields.Selection([
        ('sale', 'Customer'),
        ('purchase', 'Supplier')],
        compute='_compute_spread_type',
        required=True)
    period_number = fields.Integer(
        string='Number of Repetitions',
        default=12,
        help="Define the number of spread lines",
        required=True)
    period_type = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year')],
        default='month',
        help="Period length for the entries",
        required=True)
    use_invoice_line_account = fields.Boolean(
        string="Use invoice line's account",
    )
    credit_account_id = fields.Many2one(
        'account.account',
        string='Credit Account',
        required=True)
    debit_account_id = fields.Many2one(
        'account.account',
        string='Debit Account',
        required=True)
    is_credit_account_deprecated = fields.Boolean(
        compute='_compute_deprecated_accounts')
    is_debit_account_deprecated = fields.Boolean(
        compute='_compute_deprecated_accounts')
    unspread_amount = fields.Float(
        digits=dp.get_precision('Account'),
        compute='_compute_amounts')
    unposted_amount = fields.Float(
        digits=dp.get_precision('Account'),
        compute='_compute_amounts')
    posted_amount = fields.Float(
        digits=dp.get_precision('Account'),
        compute='_compute_amounts')
    total_amount = fields.Float(
        digits=dp.get_precision('Account'),
        compute='_compute_amounts')
    all_posted = fields.Boolean(
        compute='_compute_amounts',
        store=True)
    line_ids = fields.One2many(
        'account.spread.line',
        'spread_id',
        string='Spread Lines')
    spread_date = fields.Date(
        string='Start Date',
        default=time.strftime('%Y-01-01'),
        required=True)
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True)
    invoice_line_ids = fields.One2many(
        'account.invoice.line',
        'spread_id',
        copy=False,
        string='Invoice Lines')
    invoice_line_id = fields.Many2one(
        'account.invoice.line',
        string='Invoice line',
        compute='_compute_invoice_line',
        inverse='_inverse_invoice_line',
        store=True)
    invoice_id = fields.Many2one(
        related='invoice_line_id.invoice_id',
        readonly=True,
        store=True,
        string='Invoice')
    estimated_amount = fields.Float(digits=dp.get_precision('Account'))
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.user.company_id.currency_id.id)
    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account')
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag',
        string='Analytic Tags')
    move_line_auto_post = fields.Boolean('Auto-post lines', default=True)
    display_create_all_moves = fields.Boolean(
        compute='_compute_display_create_all_moves',
        string='Display Button All Moves')
    display_recompute_buttons = fields.Boolean(
        compute='_compute_display_recompute_buttons',
        string='Display Buttons Recompute')
    display_move_line_auto_post = fields.Boolean(
        compute='_compute_display_move_line_auto_post',
        string='Display Button Auto-post lines')
    active = fields.Boolean(default=True)

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if 'company_id' not in fields:
            company_id = self.env.user.company_id.id
        else:
            company_id = res['company_id']
        default_journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', company_id)
        ], limit=1)
        if 'journal_id' not in res and default_journal:
            res['journal_id'] = default_journal.id
        return res

    @api.depends('invoice_type')
    def _compute_spread_type(self):
        for spread in self:
            if spread.invoice_type in ['out_invoice', 'out_refund']:
                spread.spread_type = 'sale'
            else:
                spread.spread_type = 'purchase'

    @api.depends('invoice_line_ids', 'invoice_line_ids.invoice_id')
    def _compute_invoice_line(self):
        for spread in self:
            invoice_lines = spread.invoice_line_ids
            line = invoice_lines and invoice_lines[0] or False
            spread.invoice_line_id = line

    @api.multi
    def _inverse_invoice_line(self):
        for spread in self:
            invoice_line = spread.invoice_line_id
            spread.write({
                'invoice_line_ids': [(6, 0, [invoice_line.id])],
            })

    @api.depends(
        "estimated_amount",
        "currency_id",
        "company_id",
        "invoice_line_id.price_subtotal",
        "invoice_line_id.currency_id",
        "line_ids.amount",
        "line_ids.move_id.state",
    )
    def _compute_amounts(self):
        for spread in self:
            moves_amount = 0.0
            posted_amount = 0.0
            total_amount = spread.estimated_amount
            if spread.invoice_line_id:
                invoice = spread.invoice_line_id.invoice_id
                total_amount = spread.invoice_line_id.currency_id._convert(
                    spread.invoice_line_id.price_subtotal,
                    spread.currency_id,
                    spread.company_id,
                    invoice._get_currency_rate_date() or fields.Date.today()
                )

            for spread_line in spread.line_ids:
                if spread_line.move_id:
                    moves_amount += spread_line.amount
                if spread_line.move_id.state == 'posted':
                    posted_amount += spread_line.amount
            spread.unspread_amount = total_amount - moves_amount
            spread.unposted_amount = total_amount - posted_amount
            spread.posted_amount = posted_amount
            spread.total_amount = total_amount
            spread.all_posted = spread.unposted_amount == 0.0

    @api.multi
    def _compute_display_create_all_moves(self):
        for spread in self:
            if any(not line.move_id for line in spread.line_ids):
                spread.display_create_all_moves = True
            else:
                spread.display_create_all_moves = False

    @api.multi
    def _compute_display_recompute_buttons(self):
        for spread in self:
            spread.display_recompute_buttons = True
            if not spread.company_id.allow_spread_planning:
                if spread.invoice_id.state == 'draft':
                    spread.display_recompute_buttons = False

    @api.multi
    def _compute_display_move_line_auto_post(self):
        for spread in self:
            spread.display_move_line_auto_post = True
            if spread.company_id.force_move_auto_post:
                spread.display_move_line_auto_post = False

    @api.multi
    def _get_spread_entry_name(self, seq):
        """Use this method to customise the name of the accounting entry."""
        self.ensure_one()
        return (self.name or '') + '/' + str(seq)

    @api.onchange('template_id')
    def onchange_template(self):
        if self.template_id:
            if self.template_id.spread_type == 'sale':
                if self.invoice_type in ['in_invoice', 'in_refund']:
                    self.invoice_type = 'out_invoice'
            else:
                if self.invoice_type in ['out_invoice', 'out_refund']:
                    self.invoice_type = 'in_invoice'
            if self.template_id.period_number:
                self.period_number = self.template_id.period_number
            if self.template_id.period_type:
                self.period_type = self.template_id.period_type
            if self.template_id.start_date:
                self.spread_date = self.template_id.start_date

    @api.onchange('invoice_type', 'company_id')
    def onchange_invoice_type(self):
        company = self.company_id
        if not self.env.context.get('default_journal_id'):
            journal = company.default_spread_expense_journal_id
            if self.invoice_type in ('out_invoice', 'in_refund'):
                journal = company.default_spread_revenue_journal_id
            if journal:
                self.journal_id = journal

        if not self.env.context.get('default_debit_account_id'):
            if self.invoice_type in ('out_invoice', 'in_refund'):
                debit_account_id = company.default_spread_revenue_account_id
                self.debit_account_id = debit_account_id

        if not self.env.context.get('default_credit_account_id'):
            if self.invoice_type in ('in_invoice', 'out_refund'):
                credit_account_id = company.default_spread_expense_account_id
                self.credit_account_id = credit_account_id

    @api.constrains('invoice_id', 'invoice_type')
    def _check_invoice_type(self):
        for spread in self:
            if not spread.invoice_id:
                pass
            elif spread.invoice_type != spread.invoice_id.type:
                raise ValidationError(_(
                    'The Invoice Type does not correspond to the Invoice'))

    @api.constrains('journal_id')
    def _check_journal(self):
        for spread in self:
            moves = spread.mapped('line_ids.move_id').filtered('journal_id')
            if any(move.journal_id != spread.journal_id for move in moves):
                raise ValidationError(_(
                    'The Journal is not consistent with the account moves.'))

    @api.constrains('template_id', 'invoice_type')
    def _check_template_invoice_type(self):
        for spread in self:
            if spread.invoice_type in ['in_invoice', 'in_refund']:
                if spread.template_id.spread_type == 'sale':
                    raise ValidationError(_(
                        'The Spread Template (Sales) is not compatible '
                        'with selected invoice type'))
            elif spread.invoice_type in ['out_invoice', 'out_refund']:
                if spread.template_id.spread_type == 'purchase':
                    raise ValidationError(_(
                        'The Spread Template (Purchases) is not compatible '
                        'with selected invoice type'))

    @api.multi
    def _get_spread_period_duration(self):
        """Converts the selected period_type to number of months."""
        self.ensure_one()
        if self.period_type == 'year':
            return 12
        elif self.period_type == 'quarter':
            return 3
        return 1

    @api.multi
    def _init_line_date(self, posted_line_ids):
        """Calculates the initial spread date. This method
        is used by "def _compute_spread_board()" method.
        """
        self.ensure_one()
        if posted_line_ids:
            # if we already have some previous validated entries,
            # starting date is last entry + method period
            last_date = posted_line_ids[-1].date
            months = self._get_spread_period_duration()
            spread_date = last_date + relativedelta(months=months)
        else:
            spread_date = self.spread_date
        return spread_date

    @api.multi
    def _next_line_date(self, month_day, date):
        """Calculates the next spread date. This method
        is used by "def _compute_spread_board()" method.
        """
        self.ensure_one()
        months = self._get_spread_period_duration()
        date = date + relativedelta(months=months)
        # get the last day of the month
        if month_day > 28:
            max_day_in_month = calendar.monthrange(date.year, date.month)[1]
            date = date.replace(day=min(max_day_in_month, month_day))
        return date

    @api.multi
    def _compute_spread_board(self):
        """Creates the spread lines. This method is highly inspired
        from method compute_depreciation_board() present in standard
        "account_asset" module, developed by Odoo SA.
        """
        self.ensure_one()

        posted_line_ids = self.line_ids.filtered(
            lambda x: x.move_id.state == 'posted').sorted(
            key=lambda l: l.date)
        unposted_line_ids = self.line_ids.filtered(
            lambda x: not x.move_id.state == 'posted')

        # Remove old unposted spread lines.
        commands = [(2, line_id.id, False) for line_id in unposted_line_ids]

        if self.unposted_amount != 0.0:
            unposted_amount = self.unposted_amount

            spread_date = self._init_line_date(posted_line_ids)

            month_day = spread_date.day
            number_of_periods = self._get_number_of_periods(month_day)

            for x in range(len(posted_line_ids), number_of_periods):
                sequence = x + 1
                amount = self._compute_board_amount(
                    sequence, unposted_amount, number_of_periods
                )
                amount = self.currency_id.round(amount)
                rounding = self.currency_id.rounding
                if float_is_zero(amount, precision_rounding=rounding):
                    continue
                unposted_amount -= amount
                vals = {
                    'amount': amount,
                    'spread_id': self.id,
                    'name': self._get_spread_entry_name(sequence),
                    'date': self._get_last_day_of_month(spread_date),
                }
                commands.append((0, False, vals))

                spread_date = self._next_line_date(month_day, spread_date)

        self.write({'line_ids': commands})
        invoice_type_selection = dict(self.fields_get(
            allfields=['invoice_type']
        )['invoice_type']['selection'])[self.invoice_type]
        msg_body = _("Spread table '%s' created.") % invoice_type_selection
        self.message_post(body=msg_body)

    @api.multi
    def _get_number_of_periods(self, month_day):
        """Calculates the number of spread lines."""
        self.ensure_one()
        if month_day != 1:
            return self.period_number + 1
        return self.period_number

    @staticmethod
    def _get_last_day_of_month(spread_date):
        return spread_date + relativedelta(day=31)

    @api.multi
    def _compute_board_amount(self, sequence, amount, number_of_periods):
        """Calculates the amount for the spread lines."""
        self.ensure_one()
        amount_to_spread = self.total_amount
        if sequence != number_of_periods:
            amount = amount_to_spread / self.period_number
            if sequence == 1:
                date = self.spread_date
                month_days = calendar.monthrange(date.year, date.month)[1]
                days = month_days - date.day + 1
                period = self.period_number
                amount = (amount_to_spread / period) / month_days * days
        return amount

    @api.multi
    def compute_spread_board(self):
        """Checks whether the spread lines should be calculated.
        In case checks pass, invoke "def _compute_spread_board()" method.
        """
        for spread in self.filtered(lambda s: s.total_amount):
            spread._compute_spread_board()

    @api.multi
    def action_recalculate_spread(self):
        """Recalculate spread"""
        self.ensure_one()
        spread_lines = self.mapped('line_ids').filtered('move_id')
        spread_lines.unlink_move()
        self.compute_spread_board()
        self.env['account.spread.line']._create_entries()

    @api.multi
    def action_undo_spread(self):
        """Undo spreading: Remove all created moves,
        restore original account on move line"""
        self.ensure_one()
        self.mapped('line_ids').filtered('move_id').unlink_move()
        self.mapped('line_ids').unlink()

    @api.multi
    def action_unlink_invoice_line(self):
        """Unlink the invoice line from the spread board"""
        self.ensure_one()
        if self.invoice_id.state != 'draft':
            raise UserError(
                _("Cannot unlink invoice lines if the invoice is validated"))
        self._action_unlink_invoice_line()

    @api.multi
    def _action_unlink_invoice_line(self):
        spread_mls = self.mapped('line_ids.move_id.line_ids')
        spread_mls.remove_move_reconcile()
        self._message_post_unlink_invoice_line()
        self.write({'invoice_line_ids': [(5, 0, 0)]})

    def _message_post_unlink_invoice_line(self):
        for spread in self:
            invoice_id = spread.invoice_id.id
            inv_link = '<a href=# data-oe-model=account.invoice ' \
                       'data-oe-id=%d>%s</a>' % (invoice_id, _("Invoice"))
            msg_body = _("Unlinked invoice line '%s' (view %s).") % (
                spread.invoice_line_id.name, inv_link)
            spread.message_post(body=msg_body)
            spread_link = '<a href=# data-oe-model=account.spread ' \
                          'data-oe-id=%d>%s</a>' % (spread.id, _("Spread"))
            msg_body = _("Unlinked '%s' (invoice line %s).") % (
                spread_link, spread.invoice_line_id.name)
            spread.invoice_id.message_post(body=msg_body)

    @api.multi
    def unlink(self):
        if self.filtered(lambda s: s.invoice_line_id):
            raise UserError(
                _('Cannot delete spread(s) that are linked '
                  'to an invoice line.'))
        if self.mapped('line_ids.move_id').filtered(
                lambda m: m.state == 'posted'):
            raise ValidationError(
                _('Cannot delete spread(s): there are '
                  'posted Journal Entries.'))
        return super().unlink()

    @api.multi
    def reconcile_spread_moves(self):
        for spread in self:
            spread._reconcile_spread_moves()

    @api.multi
    def _reconcile_spread_moves(self, created_moves=False):
        """Reconcile spread moves if possible"""
        self.ensure_one()

        if not self.invoice_id.number:
            return

        spread_mls = self.line_ids.mapped('move_id.line_ids')
        if created_moves:
            spread_mls |= created_moves.mapped('line_ids')

        spread_sign = True if self.total_amount >= 0.0 else False
        in_invoice_or_out_refund = ('in_invoice', 'out_refund')

        if self.invoice_type in in_invoice_or_out_refund and spread_sign:
            spread_mls = spread_mls.filtered(lambda x: x.credit != 0.)
        elif self.invoice_type in in_invoice_or_out_refund:
            spread_mls = spread_mls.filtered(lambda x: x.debit != 0.)
        elif spread_sign:
            spread_mls = spread_mls.filtered(lambda x: x.debit != 0.)
        else:
            spread_mls = spread_mls.filtered(lambda x: x.credit != 0.)

        invoice_mls = self.invoice_id.move_id.mapped('line_ids')
        if self.invoice_id.type in in_invoice_or_out_refund and spread_sign:
            invoice_mls = invoice_mls.filtered(lambda x: x.debit != 0.)
        elif self.invoice_id.type in in_invoice_or_out_refund:
            invoice_mls = invoice_mls.filtered(lambda x: x.credit != 0.)
        elif spread_sign:
            invoice_mls = invoice_mls.filtered(lambda x: x.credit != 0.)
        else:
            invoice_mls = invoice_mls.filtered(lambda x: x.debit != 0.)

        to_be_reconciled = self.env['account.move.line']
        if len(invoice_mls) > 1:
            # Refine selection of move line.
            # The name is formatted the same way as it is done when creating
            # move lines in method "def invoice_line_move_line_get()" of
            # standard account module
            raw_name = self.invoice_line_id.name
            formatted_name = raw_name.split('\n')[0][:64]
            for move_line in invoice_mls:
                if move_line.name == formatted_name:
                    to_be_reconciled |= move_line
        else:
            to_be_reconciled = invoice_mls

        if len(to_be_reconciled) == 1:
            do_reconcile = spread_mls + to_be_reconciled
            do_reconcile.remove_move_reconcile()
            do_reconcile.reconcile()

    @api.multi
    def create_all_moves(self):
        for line in self.mapped('line_ids').filtered(lambda l: not l.move_id):
            line.create_move()

    @api.depends(
        'debit_account_id.deprecated', 'credit_account_id.deprecated')
    def _compute_deprecated_accounts(self):
        for spread in self:
            debit_deprecated = bool(spread.debit_account_id.deprecated)
            credit_deprecated = bool(spread.credit_account_id.deprecated)
            spread.is_debit_account_deprecated = debit_deprecated
            spread.is_credit_account_deprecated = credit_deprecated

    @api.multi
    def open_reconcile_view(self):
        self.ensure_one()
        spread_mls = self.line_ids.mapped('move_id.line_ids')
        return spread_mls.open_reconcile_view()
