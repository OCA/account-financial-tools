# Copyright 2012-2016 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError, UserError


class AccountBankReceipt(models.Model):
    _name = "account.bank.receipt"
    _description = "Account Bank Receipt"
    _order = 'receipt_date desc'

    @api.depends(
        'company_id', 'currency_id', 'order_line')
    def _compute_bank_receipt(self):
        for deposit in self:
            total = 0.0
            count = 0
            reconcile = False
            currency_none_same_company_id = False
            if deposit.company_id.currency_id != deposit.currency_id:
                currency_none_same_company_id = deposit.currency_id.id
            for line in deposit.order_line:
                count += 1
                total += line.allocation
            if deposit.move_id:
                for line in deposit.move_id.line_ids:
                    if line.debit > 0 and line.reconciled:
                        reconcile = True
            deposit.total_amount = total
            deposit.is_reconcile = reconcile
            deposit.currency_none_same_company_id =\
                currency_none_same_company_id
            deposit.check_count = count

    name = fields.Char(
        string='Name',
        size=64,
        readonly=True,
        default='/',
        copy=False
    )
    receipt_date = fields.Date(
        string='Receipt Date',
        required=True,
        states={'done': [('readonly', '=', True)]},
        default=fields.Date.context_today
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        domain=[('type', '=', 'bank'), ('bank_account_id', '=', False)],
        required=True,
        states={'done': [('readonly', '=', True)]}
    )
    journal_default_account_id = fields.Many2one(
        'account.account',
        related='journal_id.default_debit_account_id',
        string='Default Debit Account of the Journal'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        states={'done': [('readonly', '=', True)]}
    )
    currency_none_same_company_id = fields.Many2one(
        'res.currency',
        compute='_compute_bank_receipt',
        store=True,
        string='Currency (False if same as company)'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')],
        string='Status',
        default='draft',
        readonly=True
    )
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True
    )
    bank_journal_id = fields.Many2one(
        'account.journal',
        string='Bank Account',
        required=True,
        domain="[('company_id', '=', company_id), ('type', '=', 'bank'), "
        "('bank_account_id', '!=', False)]",
        states={'done': [('readonly', '=', True)]}
    )
    line_ids = fields.One2many(
        'account.move.line',
        related='move_id.line_ids',
        string='Lines',
        readonly=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        states={'done': [('readonly', '=', True)]},
        default=lambda self: self.env['res.company']._company_default_get()
    )
    total_amount = fields.Float(
        compute='_compute_bank_receipt',
        string='Total Amount',
        readonly=True,
        store=True,
        digits=dp.get_precision('Account')
    )
    check_count = fields.Integer(
        compute='_compute_bank_receipt',
        readonly=True,
        store=True,
        string='Number of Checks'
    )
    is_reconcile = fields.Boolean(
        compute='_compute_bank_receipt',
        readonly=True,
        store=True,
        string='Reconcile'
    )
    partner_id = fields.Many2one(
        'res.partner',
        domain="[('customer', '=', True)]",
        string='Partner',
        required=True,
        states={'done': [('readonly', True)]}
    )
    order_line = fields.One2many(
        'account.bank.receipt.line',
        'order_id',
        string='Order Lines',
        states={'done': [('readonly', True)]}
    )

    @api.constrains('order_line')
    def _check_allocation(self):
        for rec in self:
            payments = rec.order_line.mapped('account_move_line_ids')
            for payment in payments:
                allocation = \
                    sum(rec.order_line.filtered(
                        lambda l: l.account_move_line_ids.id == payment.id
                    ).mapped('allocation'))
                residual = payment.amount_residual
                if allocation > residual:
                    raise ValidationError(
                        _("%s has sum Allocation > Residual") % (
                            payment.name))

    @api.constrains('currency_id', 'company_id')
    def _check_deposit(self):
        for deposit in self:
            deposit_currency = deposit.currency_id
            if deposit_currency == deposit.company_id.currency_id:
                for line in deposit.order_line:
                    if line.account_move_line_ids.currency_id:
                        raise ValidationError(
                            _("The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s.") % (
                                line.allocation, line.ref or '',
                                line.account_move_line_ids.currency_id.name,
                                deposit_currency.name))
            else:
                for line in deposit.order_line:
                    if line.account_move_line_ids.currency_id != \
                         deposit_currency:
                        raise ValidationError(
                            _("The check with amount %s and reference '%s' "
                                "is in currency %s but the deposit is in "
                                "currency %s.") % (
                                line.allocation, line.ref or '',
                                line.account_move_line_ids.currency_id.name,
                                deposit_currency.name))

    def unlink(self):
        for deposit in self:
            if deposit.state == 'done':
                raise UserError(
                    _("The deposit '%s' is in valid state, so you must "
                        "cancel it before deleting it.")
                    % deposit.name)
        return super(AccountBankReceipt, self).unlink()

    def backtodraft(self):
        for deposit in self:
            if deposit.move_id:
                # It will raise here if journal_id.update_posted = False
                deposit.move_id.button_cancel()
                for line in deposit.order_line:
                    if line.reconciled:
                        line.remove_move_reconcile()
                deposit.move_id.unlink()
            deposit.write({'state': 'draft'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].\
                with_context(ir_sequence_date=vals.get('receipt_date')).\
                next_by_code('account.bank.receipt')
        return super(AccountBankReceipt, self).create(vals)

    @api.model
    def _prepare_account_move_vals(self, deposit):
        if (
                deposit.company_id.bank_receipt_offsetting_account ==
                'bank_account'):
            journal_id = deposit.bank_journal_id.id
        else:
            journal_id = deposit.journal_id.id
        move_vals = {
            'journal_id': journal_id,
            'date': deposit.receipt_date,
            'ref': _('Bank Receipt %s') % deposit.name,
        }
        return move_vals

    @api.model
    def _prepare_move_line_vals(self, line, rate_currency):
        assert \
            (line.allocation > 0), 'Allocation must have a value'
        if rate_currency:
            return {
                'name': _('Bank Receipt - Ref. Check %s')
                % line.account_move_line_ids.ref,
                'credit': line.allocation/rate_currency,
                'debit': 0.0,
                'account_id': line.account_move_line_ids.account_id.id,
                'partner_id': line.account_move_line_ids.partner_id.id,
                'currency_id':
                    line.account_move_line_ids.currency_id.id or False,
                'amount_currency': line.allocation * -1,
            }
        return {
            'name': _('Bank Receipt - Ref. Check %s')
            % line.account_move_line_ids.ref,
            'credit': line.allocation,
            'debit': 0.0,
            'account_id': line.account_move_line_ids.account_id.id,
            'partner_id': line.account_move_line_ids.partner_id.id,
            'currency_id': line.account_move_line_ids.currency_id.id or False,
            'amount_currency': False,
        }

    @api.model
    def _prepare_counterpart_move_lines_vals(
            self, deposit, total_amount, total_amount_currency):
        company = deposit.company_id
        if not company.bank_receipt_offsetting_account:
            raise UserError(_(
                "You must configure the 'Bank Receipt Offsetting Account' "
                "on the Accounting Settings page"))
        if company.bank_receipt_offsetting_account == 'bank_account':
            if not deposit.bank_journal_id.default_debit_account_id:
                raise UserError(_(
                    "Missing 'Default Debit Account' on bank journal '%s'")
                    % deposit.bank_journal_id.name)
            account_id = deposit.bank_journal_id.default_debit_account_id.id
        elif company.bank_receipt_offsetting_account == 'transfer_account':
            if not company.bank_receipt_transfer_account_id:
                raise UserError(_(
                    "Missing 'Bank Receipt Offsetting Account' on the "
                    "company '%s'.") % company.name)
            account_id = company.bank_receipt_transfer_account_id.id
        return {
            'name': _('Bank Receipt %s') % deposit.name,
            'debit': total_amount,
            'credit': 0.0,
            'account_id': account_id,
            'partner_id': False,
            'currency_id': deposit.currency_none_same_company_id.id or False,
            'amount_currency': total_amount_currency,
        }

    def validate_deposit(self):
        am_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        for deposit in self:
            move_vals = self._prepare_account_move_vals(deposit)
            move = am_obj.create(move_vals)
            total_amount = 0.0
            total_amount_currency = 0.0
            rate_currency = False
            to_reconcile_lines = []
            if deposit.company_id.currency_id != deposit.currency_id:
                rate_currency = self.currency_id._get_conversion_rate(
                    self.company_id.currency_id, self.currency_id,
                    self.company_id, self.receipt_date)
            for line in deposit.order_line:
                if rate_currency:
                    total_amount += line.allocation/rate_currency
                    total_amount_currency += line.allocation
                else:
                    total_amount += line.allocation
                line_vals = self._prepare_move_line_vals(line, rate_currency)
                line_vals['move_id'] = move.id
                move_line = move_line_obj.with_context(
                    check_move_validity=False).create(line_vals)
                to_reconcile_lines.append(
                    line.account_move_line_ids + move_line)

            # Create counter-part
            counter_vals = self._prepare_counterpart_move_lines_vals(
                deposit, total_amount, total_amount_currency)
            counter_vals['move_id'] = move.id
            move_line_obj.create(counter_vals)
            if deposit.company_id.bank_receipt_post_move:
                move.post()

            deposit.write({'state': 'done', 'move_id': move.id})
            for reconcile_lines in to_reconcile_lines:
                reconcile_lines.reconcile()
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

    def get_report(self):
        report = self.env.ref(
            'account_bank_receipt.report_account_bank_receipt')
        action = report.report_action(self)
        return action


class AccountBankReceiptLine(models.Model):
    _name = "account.bank.receipt.line"
    _description = "Account Bank Receipt Line"
    _order = 'order_id, id'

    order_id = fields.Many2one(
        'account.bank.receipt',
        string='Order Reference',
        copy=False,
    )
    account_move_line_ids = fields.Many2one(
        'account.move.line',
        string='Move Lines',
        required=True
    )
    date_payment = fields.Date(
        string='Date',
        related='account_move_line_ids.date'
    )
    due_date_payment = fields.Date(
        string='Due Date',
        related='account_move_line_ids.date_maturity'
    )
    ref_payment = fields.Char(
        string='Reference',
        related='account_move_line_ids.ref'
    )
    amount_payment = fields.Float(
        string='Amount',
        compute='_compute_move_line',
        store=True
    )
    amount_residual = fields.Float(
        string='Residual',
        compute='_compute_move_line',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='account_move_line_ids.currency_id',
        store=True
    )
    type = fields.Selection([
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('check', 'Check')],
        string='Type',
        required=True
    )
    check_number = fields.Char(
        string='Check No.'
    )
    allocation = fields.Float(
        string='Allocation',
        required=True
    )
    full_reconcile_id = fields.Many2one(
        'account.full.reconcile',
        related='account_move_line_ids.full_reconcile_id',
        string='Matching Number'
    )

    @api.depends('account_move_line_ids')
    def _compute_move_line(self):
        for rec in self:
            amount = 0.0
            amount_residual = 0.0
            if rec.order_id.company_id.currency_id != rec.order_id.currency_id:
                amount = rec.account_move_line_ids.amount_currency
                amount_residual = \
                    rec.account_move_line_ids.amount_residual_currency
            else:
                amount = rec.account_move_line_ids.debit
                amount_residual = rec.account_move_line_ids.amount_residual
            rec.amount_payment = amount
            rec.amount_residual = amount_residual
