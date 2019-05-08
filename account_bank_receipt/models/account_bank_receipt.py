# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import _, api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError, UserError


class AccountBankReceipt(models.Model):
    _name = 'account.bank.receipt'
    _description = 'Account Bank Receipt'
    _order = 'receipt_date desc'

    @api.depends('company_id', 'currency_id', 'receipt_line_ids')
    def _compute_bank_receipt(self):
        for bank_transit in self:
            total = 0.0
            count = 0
            reconcile = False
            currency_none_same_company_id = False
            if bank_transit.company_id.currency_id != bank_transit.currency_id:
                currency_none_same_company_id = bank_transit.currency_id.id
            for line in bank_transit.receipt_line_ids:
                count += 1
                total += line.allocation
            if bank_transit.move_id:
                for line in bank_transit.move_id.line_ids:
                    if line.debit > 0 and line.reconciled:
                        reconcile = True
            bank_transit.total_amount = total
            bank_transit.is_reconcile = reconcile
            bank_transit.currency_none_same_company_id =\
                currency_none_same_company_id
            bank_transit.in_transit = count

    name = fields.Char(
        size=64,
        default='/',
        readonly=True,
        copy=False,
    )
    receipt_date = fields.Date(
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
        compute='_compute_bank_receipt',
        store=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done')],
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
        compute='_compute_bank_receipt',
        readonly=True,
        store=True,
        digits=dp.get_precision('Product Price'),
    )
    in_transit = fields.Integer(
        compute='_compute_bank_receipt',
        readonly=True,
        store=True,
    )
    is_reconcile = fields.Boolean(
        string='Reconcile',
        compute='_compute_bank_receipt',
        readonly=True,
        store=True,
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('customer', '=', True)]",
        required=True,
        states={'done': [('readonly', True)]},
    )
    receipt_line_ids = fields.One2many(
        comodel_name='account.bank.receipt.line',
        inverse_name='order_id',
        states={'done': [('readonly', True)]},
    )

    @api.constrains('receipt_line_ids')
    def _check_allocation(self):
        for rec in self:
            payments = rec.receipt_line_ids.mapped('move_line_id')
            for payment in payments:
                allocation = sum(rec.receipt_line_ids.filtered(
                    lambda l: l.move_line_id.id == payment.id
                    ).mapped('allocation'))
                residual = payment.amount_residual
                if allocation > residual:
                    raise ValidationError(_(
                        '%s has sum Allocation > Residual'
                        ) % (payment.move_id.name))

    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise UserError(
                    _("The bank transit '%s' is in valid state, so you must "
                      "cancel it before deleting it.") % rec.name)
        return super(AccountBankReceipt, self).unlink()

    @api.multi
    def backtodraft(self):
        for rec in self:
            if rec.move_id:
                rec.move_id.button_cancel()
                rec.move_id.line_ids.filtered(
                    lambda x: x.account_id.reconcile).remove_move_reconcile()
                rec.move_id.unlink()
            rec.write({'state': 'draft'})
        return True

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].\
                with_context(ir_sequence_date=vals.get('receipt_date')).\
                next_by_code('account.bank.receipt')
        return super(AccountBankReceipt, self).create(vals)

    @api.model
    def _prepare_account_move_vals(self, bank_transit):
        offsetting_account = \
            bank_transit.company_id.bank_receipt_offsetting_account
        if offsetting_account == 'bank_account':
            journal_id = bank_transit.bank_journal_id.id
        else:
            journal_id = bank_transit.journal_id.id
        move_vals = {
            'journal_id': journal_id,
            'date': bank_transit.receipt_date,
            'ref': _('Bank Receipt %s') % bank_transit.name,
        }
        return move_vals

    @api.model
    def _prepare_move_line_vals(self, line, rate_currency):
        assert (line.allocation > 0), 'Allocation must have a value'
        if rate_currency:
            return {
                'name': _('Bank Receipt - Ref. Invoice %s')
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
            'name': _('Bank Receipt - Ref. Invoice %s')
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
        if not company.bank_receipt_offsetting_account:
            raise UserError(_(
                "You must configure the 'Bank Receipt Offsetting Account' "
                "on the Accounting Settings page"))
        if company.bank_receipt_offsetting_account == 'bank_account':
            if not bank_transit.bank_journal_id.default_debit_account_id:
                raise UserError(_(
                    "Missing 'Default Debit Account' on bank journal '%s'")
                    % bank_transit.bank_journal_id.name)
            account_id = \
                bank_transit.bank_journal_id.default_debit_account_id.id
        elif company.bank_receipt_offsetting_account == 'transfer_account':
            if not company.bank_receipt_transfer_account_id:
                raise UserError(_(
                    "Missing 'Bank Receipt Offsetting Account' on the "
                    "company '%s'.") % company.name)
            account_id = company.bank_receipt_transfer_account_id.id
        return {
            'name': _('Bank Receipt %s') % bank_transit.name,
            'debit': total_amount,
            'credit': 0.0,
            'account_id': account_id,
            'partner_id': False,
            'currency_id':
                bank_transit.currency_none_same_company_id.id or False,
            'amount_currency': total_amount_currency,
        }

    def validate_bank_transit(self):
        am_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        for bank_transit in self:
            move_vals = self._prepare_account_move_vals(bank_transit)
            move = am_obj.create(move_vals)
            total_amount = 0.0
            total_amount_currency = 0.0
            rate_currency = False
            to_reconcile_lines = []
            if bank_transit.company_id.currency_id != bank_transit.currency_id:
                rate_currency = self.currency_id._get_conversion_rate(
                    self.company_id.currency_id, self.currency_id,
                    self.company_id, self.receipt_date)
            if rate_currency:
                total_amount = bank_transit.total_amount/rate_currency
                total_amount_currency = bank_transit.total_amount
            else:
                total_amount = bank_transit.total_amount

            for line in bank_transit.receipt_line_ids:
                line_vals = self._prepare_move_line_vals(line, rate_currency)
                line_vals['move_id'] = move.id
                move_line = move_line_obj.with_context(
                    check_move_validity=False).create(line_vals)
                to_reconcile_lines.append(line.move_line_id + move_line)

            # Create counter-part
            counter_vals = self._prepare_counterpart_move_lines_vals(
                bank_transit, total_amount, total_amount_currency)
            counter_vals['move_id'] = move.id
            move_line_obj.create(counter_vals)
            if bank_transit.company_id.bank_receipt_post_move:
                move.post()

            bank_transit.write({'state': 'done', 'move_id': move.id})
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


class AccountBankReceiptLine(models.Model):
    _name = 'account.bank.receipt.line'
    _description = 'Account Bank Receipt Line'
    _order = 'order_id, id'

    order_id = fields.Many2one(
        comodel_name='account.bank.receipt',
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
    due_date_payment = fields.Date(
        string='Due Date',
        related='move_line_id.date_maturity',
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
    receipt_type = fields.Selection([
        ('cash', 'Cash'),
        ('transfer', 'Transfer'),
        ('check', 'Check')],
        string='Type',
        required=True,
    )
    check_number = fields.Char(
        string='Check No.',
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
            if rec.order_id.company_id.currency_id != rec.order_id.currency_id:
                amount = rec.move_line_id.amount_currency
                amount_residual = rec.move_line_id.amount_residual_currency
            else:
                amount = rec.move_line_id.debit
                amount_residual = rec.move_line_id.amount_residual
            rec.amount_payment = amount
            rec.amount_residual = amount_residual
