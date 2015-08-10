# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp


class account_transfer_wizard(models.Model):

    _name = "account.transfer.wizard"
    _description = "account.transfer.wizard"

    date = fields.Date(
        'Date',
        )
    period_id = fields.Many2one(
        'account.period',
        'Period',
        help='If not period defined, a period for this date will be used',
        # required=True,
        # readonly=True,
        # states={'draft': [('readonly', False)]},
        )
    from_journal_id = fields.Many2one(
        'account.journal',
        'To Journal',
        required=True,
        ondelete='cascade',
        domain=[('type', 'in', ['bank', 'cash'])],
        )
    to_journal_id = fields.Many2one(
        'account.journal',
        'From Journal',
        required=True,
        ondelete='cascade',
        domain=[('type', 'in', ['bank', 'cash'])],
        )
    amount = fields.Float(
        'Amount',
        required=True,
        readonly=True,
        digits=dp.get_precision('Account'),
        )

    @api.constrains('from_journal_id', 'to_journal_id')
    def check_companies(self):
        if self.from_journal_id.company_id != self.to_journal_id.company_id:
            raise Warning(_('Both Journals must belong to the same company!'))

    @api.multi
    def confirm(self):
        self.ensure_one()
        transfer_account = self.from_journal_id.company_id.transfer_account_id
        if not transfer_account:
            raise Warning(_(
                'No transfer account configured con company %s!') % (
                self.from_journal_id.company_i.name))

    @api.multi
    def get_move_vals(self, journal, debit_amount, credit_amount):
        self.ensure_one()

        if not self.date:
            self.date = fields.Date.context_today(self)

        period = self.period_id
        if not self.period_id:
            period = period.with_context(company_id=journal.company_id.id).find(
                self.date)[:1]

        if not period:
            raise Warning(_('Not period found for current date'))

        name = journal.sequence_id._next()
        move_vals = {
            'ref': name,
            'name': _('Journal Transfer'),
            'period_id': period.id,
            'date': self.date,
            'journal_id': journal.id,
            'company_id': journal.company_id.id,
            }
        line1_vals = {
            # 'name': self.tax_settlement_id.name,
            'debit': debit,
            'credit': credit,
            'account_id': line['account_id'][0],
            'tax_code_id': self.tax_code_id.id,
            'tax_amount': -1.0 * line['tax_amount'],
        }
        return move_vals
