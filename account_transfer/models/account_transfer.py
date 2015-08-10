# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp


class account_transfer(models.Model):

    _name = "account.transfer"
    _description = "account.transfer"
    _inherit = ['mail.thread']

    name = fields.Char(
        'Name',
        # default=_('Journal Transfer'),
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    date = fields.Date(
        'Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    period_id = fields.Many2one(
        'account.period',
        'Period',
        help='If not period defined, a period for this date will be used',
        readonly=True,
        states={'draft': [('readonly', False)]},
        )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env[
            'res.company']._company_default_get('account.transfer'),
        )
    source_journal_id = fields.Many2one(
        'account.journal',
        'Source Journal',
        required=True,
        ondelete='cascade',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('type', 'in', ['bank', 'cash']), "
        "('company_id', '=', company_id)]",
        )
    target_journal_id = fields.Many2one(
        'account.journal',
        'Target Journal',
        required=True,
        ondelete='cascade',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain="[('type', 'in', ['bank', 'cash']), "
        "('company_id', '=', company_id), ('id', '!=', source_journal_id)]",

        )
    source_move_id = fields.Many2one(
        'account.move',
        'Source Move',
        readonly=True,
        )
    target_move_id = fields.Many2one(
        'account.move',
        'Target Move',
        readonly=True,
        )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancel')],
        'State',
        required=True,
        readonly=True,
        default='draft'
        )
    note = fields.Html(
        'Notes'
        )
    amount = fields.Float(
        'Amount',
        required=True,
        digits=dp.get_precision('Account'),
        readonly=True,
        states={'draft': [('readonly', False)]},
        )

    @api.one
    @api.constrains('source_journal_id', 'target_journal_id')
    def check_companies(self):
        if (
                self.source_journal_id.company_id != self.company_id or
                self.target_journal_id.company_id != self.company_id):
            raise Warning(_('Both Journals must belong to the same company!'))
        if self.source_journal_id == self.target_journal_id:
            raise Warning(_('Source and Target Journal must be different!'))

    @api.multi
    def action_confirm(self):
        self.ensure_one()

        if self.amount <= 0.0:
            raise Warning(_('Amount must be greater than 0!'))

        # set date if not configured
        if not self.date:
            self.date = fields.Date.context_today(self)

        # set period if not configured
        period = self.period_id
        if not self.period_id:
            period = period.with_context(
                company_id=self.company_id.id).find(
                self.date)[:1]
            if not period:
                raise Warning(_('Not period found for current date'))
            self.period_id = period.id

        # create source move
        source_move = self.source_move_id.create(self.get_move_vals('source'))

        # create target move
        target_move = self.target_move_id.create(self.get_move_vals('target'))

        self.write({
            'target_move_id': target_move.id,
            'source_move_id': source_move.id,
            'state': 'confirmed',
            })

    @api.multi
    def get_move_vals(self, move_type):
        self.ensure_one()

        transfer_account = self.company_id.transfer_account_id
        if not transfer_account:
            raise Warning(_(
                'No transfer account configured con company %s!') % (
                self.source_journal_id.company_id.name))

        if move_type == 'source':
            ref = _('%s (Source)' % self.name)
            journal = self.source_journal_id
            first_account = journal.default_debit_account_id
            second_account = transfer_account
        if move_type == 'target':
            ref = _('%s (Target)' % self.name)
            journal = self.target_journal_id
            first_account = transfer_account
            second_account = journal.default_credit_account_id

        name = journal.sequence_id._next()
        move_vals = {
            'ref': ref,
            'name': name,
            'period_id': self.period_id.id,
            'date': self.date,
            'journal_id': journal.id,
            'company_id': self.company_id.id,
            }
        first_line_vals = {
            'name': name,
            'debit': 0.0,
            'credit': self.amount,
            'account_id': first_account.id,
        }
        second_line_vals = {
            'name': name,
            'debit': self.amount,
            'credit': 0.0,
            'account_id': second_account.id,
        }
        move_vals['line_id'] = [
            (0, _, first_line_vals), (0, _, second_line_vals)]
        return move_vals

    @api.multi
    def action_to_draft(self):
        self.write({'state': 'draft'})
        return True

    @api.one
    def action_cancel(self):
        self.source_move_id.unlink()
        self.target_move_id.unlink()
        self.state = 'cancel'
