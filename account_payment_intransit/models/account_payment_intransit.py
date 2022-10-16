# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError, UserError


class AccountPaymentIntransit(models.Model):
    _name = 'account.payment.intransit'
    _description = 'Account Payment Intransit'
    _order = 'intransit_date, id desc'

    name = fields.Char(
        size=64,
        default='/',
        readonly=True,
        copy=False,
    )
    intransit_date = fields.Date(
        string='Date',
        required=True,
        states={'done': [('readonly', '=', True)]},
        default=fields.Date.context_today,
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain=[('type', '=', 'bank'), ('bank_account_id', '=', False)],
        required=True,
        states={'done': [('readonly', '=', True)]},
        copy=False,
    )
    journal_default_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Default Debit Account of the Journal',
        related='journal_id.default_debit_account_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        required=True,
        states={'done': [('readonly', '=', True)]},
    )
    currency_none_same_company_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency (False if same as company)',
        compute='_compute_payment_intransit',
        store=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')],
        string='Status',
        default='draft',
        readonly=True,
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Journal Entry',
        readonly=True,
    )
    bank_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Bank Account',
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'bank'), "
               "('bank_account_id', '!=', False)]",
        states={'done': [('readonly', '=', True)]}
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True,
        states={'done': [('readonly', '=', True)]},
        default=lambda self: self.env['res.company']._company_default_get(),
    )
    total_amount = fields.Monetary(
        compute='_compute_payment_intransit',
        readonly=True,
        store=True,
        digits=dp.get_precision('Product Price'),
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('customer', '=', True)]",
        required=True,
        states={'done': [('readonly', True)]},
    )
    intransit_line_ids = fields.One2many(
        comodel_name='account.payment.intransit.line',
        inverse_name='intransit_id',
        states={'done': [('readonly', True)]},
    )

    @api.depends('company_id', 'currency_id', 'intransit_line_ids')
    def _compute_payment_intransit(self):
        for bank_transit in self:
            currency_none_same_company_id = False
            if bank_transit.company_id.currency_id != bank_transit.currency_id:
                currency_none_same_company_id = bank_transit.currency_id.id
            total = sum(bank_transit.intransit_line_ids.mapped('allocation'))
            bank_transit.total_amount = total
            bank_transit.currency_none_same_company_id =\
                currency_none_same_company_id

    @api.constrains('intransit_line_ids')
    def _check_allocation(self):
        for rec in self:
            move_line = rec.intransit_line_ids.mapped('move_line_id')
            for ml in move_line:
                allocation = sum(rec.intransit_line_ids.filtered(
                    lambda l: l.move_line_id.id == ml.id).mapped('allocation'))
                residual = ml.amount_residual
                if allocation > residual:
                    raise ValidationError(_(
                        '%s has sum allocation more than residual'
                        ) % (ml.payment_id.name))

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    _("The bank transit '%s' is in valid state, so you must "
                      "cancel it before deleting it.") % rec.name)
        return super(AccountPaymentIntransit, self).unlink()

    @api.multi
    def action_intransit_cancel(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.line_ids.filtered(
                    lambda x: x.account_id.reconcile).remove_move_reconcile()
                rec.move_id.unlink()
            rec.write({'state': 'cancel'})
        return True

    @api.multi
    def backtodraft(self):
        return self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].\
                with_context(ir_sequence_date=vals.get('intransit_date')).\
                next_by_code('account.payment.intransit')
        return super(AccountPaymentIntransit, self).create(vals)

    @api.model
    def _prepare_account_move_vals(self, bank_transit):
        offsetting_account = \
            bank_transit.company_id.payment_intransit_offsetting_account
        if offsetting_account == 'bank_account':
            journal_id = bank_transit.bank_journal_id.id
        else:
            journal_id = bank_transit.journal_id.id
        move_vals = {
            'journal_id': journal_id,
            'date': bank_transit.intransit_date,
            'ref': _('Payment Intransit %s') % bank_transit.name,
        }
        return move_vals

    @api.model
    def _prepare_move_line_vals(self, line, rate_currency=None):
        assert (line.allocation > 0), 'Allocation must have a value'
        if rate_currency:
            return {
                'name': _('Payment Intransit - Ref. Invoice %s')
                % line.move_line_id.ref,
                'credit': line.allocation/rate_currency,
                'debit': 0.0,
                'account_id': line.move_line_id.account_id.id,
                'partner_id': line.move_line_id.partner_id.id,
                'currency_id':
                    line.move_line_id.currency_id.id or False,
                'amount_currency': line.allocation * -1,
            }
        return {
            'name': _('Payment Intransit - Ref. Invoice %s')
            % line.move_line_id.ref,
            'credit': line.allocation,
            'debit': 0.0,
            'account_id': line.move_line_id.account_id.id,
            'partner_id': line.move_line_id.partner_id.id,
            'currency_id': line.move_line_id.currency_id.id or False,
            'amount_currency': False,
        }

    @api.model
    def _prepare_counterpart_move_lines_vals(
            self, bank_transit, total_amount, total_amount_currency):
        company = bank_transit.company_id
        payment_intransit_account = \
            company.payment_intransit_offsetting_account
        if not payment_intransit_account:
            raise UserError(_(
                "You must configure the 'Payment Intransit Offsetting Account'"
                " on the Accounting Settings page"))
        if payment_intransit_account == 'bank_account':
            if not bank_transit.bank_journal_id.default_debit_account_id:
                raise UserError(_(
                    "Missing 'Default Debit Account' on bank journal '%s'")
                    % bank_transit.bank_journal_id.name)
            account_id = \
                bank_transit.bank_journal_id.default_debit_account_id.id
        elif payment_intransit_account == 'transfer_account':
            if not company.payment_intransit_transfer_account_id:
                raise UserError(_(
                    "Missing 'Payment Intransit Offsetting Account' on the "
                    "company '%s'.") % company.name)
            account_id = company.payment_intransit_transfer_account_id.id
        return {
            'name': _('Payment Intransit %s') % bank_transit.name,
            'debit': total_amount,
            'credit': 0.0,
            'account_id': account_id,
            'partner_id': False,
            'currency_id':
                bank_transit.currency_none_same_company_id.id or False,
            'amount_currency': total_amount_currency,
        }

    @api.model
    def _create_writeoff_move_line_hook(self, move, rate_currency=None):
        return True

    @api.model
    def _do_reconcile(self, to_reconcile_lines):
        for reconcile_lines in to_reconcile_lines:
            reconcile_lines.reconcile()
        return True

    def validate_payment_intransit(self):
        am_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        for bank_transit in self:
            if not bank_transit.intransit_line_ids:
                raise ValidationError(_('No lines!'))
            move_vals = self._prepare_account_move_vals(bank_transit)
            move = am_obj.create(move_vals)
            total_amount = 0.0
            total_amount_currency = 0.0
            rate_currency = False
            to_reconcile_lines = []

            # check currency
            if bank_transit.company_id.currency_id != bank_transit.currency_id:
                rate_currency = self.currency_id._get_conversion_rate(
                    self.company_id.currency_id, self.currency_id,
                    self.company_id, self.intransit_date)
            # check if rate = 0
            if rate_currency:
                total_amount = bank_transit.total_amount/rate_currency
                total_amount_currency = bank_transit.total_amount
            else:
                total_amount = bank_transit.total_amount

            for line in bank_transit.intransit_line_ids:
                line_vals = self._prepare_move_line_vals(line, rate_currency)
                line_vals['move_id'] = move.id
                move_line = move_line_obj.with_context(
                    check_move_validity=False).create(line_vals)
                to_reconcile_lines.append(line.move_line_id + move_line)

            # Prepare for hook
            bank_transit._create_writeoff_move_line_hook(move, rate_currency)
            # Create counter-part
            counter_vals = self._prepare_counterpart_move_lines_vals(
                bank_transit, total_amount, total_amount_currency)
            counter_vals['move_id'] = move.id
            move_line_obj.create(counter_vals)
            if bank_transit.company_id.payment_intransit_post_move:
                move.post()

            bank_transit.write({'state': 'done', 'move_id': move.id})
            bank_transit._do_reconcile(to_reconcile_lines)
        return True

    @api.onchange('company_id')
    def onchange_company_id(self):
        if self.company_id:
            bank_journals = self.env['account.journal'].search([
                ('company_id', '=', self.company_id.id),
                ('type', '=', 'bank'),
                ('bank_account_id', '!=', False)])
            if len(bank_journals) == 1:
                self.bank_journal_id = bank_journals[0]
        else:
            self.bank_journal_id = False

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id
            else:
                self.currency_id = self.journal_id.company_id.currency_id


class AccountPaymentIntransitLine(models.Model):
    _name = 'account.payment.intransit.line'
    _description = 'Account Payment Intransit Line'
    _order = 'intransit_id, id'

    intransit_id = fields.Many2one(
        comodel_name='account.payment.intransit',
        string='Order Reference',
        copy=False,
    )
    move_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string='Move Lines',
        required=True,
    )
    date_payment = fields.Date(
        string='Date',
        related='move_line_id.date',
    )
    ref_payment = fields.Char(
        string='Reference',
        related='move_line_id.ref',
    )
    amount_payment = fields.Monetary(
        string='Amount',
        compute='_compute_move_line',
        store=True,
    )
    amount_residual = fields.Monetary(
        string='Residual',
        compute='_compute_move_line',
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='move_line_id.currency_id',
        store=True,
    )
    payment_intransit_type = fields.Selection([
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('check', 'Check')],
        string='Type',
        required=True,
    )
    check_number = fields.Char(
        string='Check No.',
        help='Record number of check',
    )
    bank_branch = fields.Char(
        string='Bank/Branch',
        help='Record bank/branch of origin',
    )
    allocation = fields.Monetary(
        string='Allocation',
        required=True,
    )
    full_reconcile_id = fields.Many2one(
        comodel_name='account.full.reconcile',
        related='move_line_id.full_reconcile_id',
        string='Matching Number',
    )

    @api.depends('move_line_id')
    def _compute_move_line(self):
        for rec in self:
            amount = 0.0
            amount_residual = 0.0
            company_curr = rec.intransit_id.company_id.currency_id
            if company_curr != rec.intransit_id.currency_id:
                amount = rec.move_line_id.amount_currency
                amount_residual = rec.move_line_id.amount_residual_currency
            else:
                amount = rec.move_line_id.debit
                amount_residual = rec.move_line_id.amount_residual
            rec.amount_payment = amount
            rec.amount_residual = amount_residual
