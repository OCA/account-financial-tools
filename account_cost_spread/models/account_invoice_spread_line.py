# -*- coding: utf-8 -*-
# © 2014 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceSpreadLine(models.Model):
    _name = 'account.invoice.spread.line'
    _description = 'Account Invoice Spread Lines'

    _order = 'type, line_date'

    name = fields.Char('Spread Name', size=64, readonly=True)
    invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Invoice Line',
        required=True)
    previous_id = fields.Many2one(
        comodel_name='account.invoice.spread.line',
        string='Previous Spread Line',
        readonly=True)
    amount = fields.Float(
        string='Amount',
        digits_compute=dp.get_precision('Account'),
        required=True)
    remaining_value = fields.Float(
        string='Next Period Spread',
        digits_compute=dp.get_precision('Account'))
    spreaded_value = fields.Float(
        string='Amount Already Spread',
        digits_compute=dp.get_precision('Account'))
    line_date = fields.Date(
        string='Date',
        required=True)
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Spread Entry', readonly=True)
    move_check = fields.Boolean(
        compute='_move_check',
        string='Posted',
        store=True)
    type = fields.Selection(
        [('create', 'Value'),
         ('depreciate', 'Depreciation'),
         ('remove', 'Asset Removal'),
         ],
        string='Type',
        readonly=True,
        defaults='depreciate')
    init_entry = fields.Boolean(
        string='Initial Balance Entry',
        help="Set this flag for entries of previous fiscal years "
             "for which OpenERP has not generated accounting entries.")

    @api.depends('move_id')
    @api.one
    def _move_check(self):
        if self.move_id:
            self.move_check = True
        else:
            self.move_check = False

    @api.model
    def _setup_move_data(self, spread_line, spread_date,
                         period_id):

        invoice = spread_line.invoice_line_id.invoice_id

        move_data = {
            'name': invoice.internal_number,
            'date': spread_date,
            'ref': spread_line.name,
            'period_id': period_id,
            'journal_id': invoice.journal_id.id,
            }
        return move_data

    @api.model
    def _setup_move_line_data(self, spread_line, spread_date,
                              period_id, account_id, type, move_id):
        invoice_line = spread_line.invoice_line_id

        if type == 'debit':
            debit = spread_line.amount
            credit = 0.0
        elif type == 'credit':
            debit = 0.0
            credit = spread_line.amount

        move_line_data = {
            'name': invoice_line.name,
            'ref': spread_line.name,
            'move_id': move_id,
            'account_id': account_id,
            'credit': credit,
            'debit': debit,
            'period_id': period_id,
            'journal_id': invoice_line.invoice_id.journal_id.id,
            'partner_id': invoice_line.invoice_id.partner_id.id,
            'date': spread_date,
            }
        return move_line_data

    @api.multi
    def create_move(self):
        """Used by a button to manually create a move from a spread line entry.
        Also called by a cron job."""
        period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
#         currency_obj = self.env['res.currency']
        created_move_ids = []

        for line in self:

            invoice_line = line.invoice_line_id
            spread_date = line.line_date

            period_ids = period_obj.with_context(
                account_period_prefer_normal=True).find(
                spread_date
            )
            period_id = period_ids and period_ids[0] or False
            move_id = move_obj.create(
                self._setup_move_data(line, spread_date, period_id.id)
            )
            _logger.debug('MoveID: %s', (move_id.id))

            if invoice_line.invoice_id.type in ('in_invoice', 'out_refund'):
                debit_acc_id = invoice_line.account_id.id
                credit_acc_id = invoice_line.spread_account_id.id
            else:
                debit_acc_id = invoice_line.spread_account_id.id
                credit_acc_id = invoice_line.account_id.id

            move_line_obj.create(
                self._setup_move_line_data(
                    line, spread_date, period_id.id, debit_acc_id,
                    'debit', move_id.id
                )
            )
            move_line_obj.create(
                self._setup_move_line_data(
                    line, spread_date, period_id.id, credit_acc_id,
                    'credit', move_id.id
                )
            )

            # Add move_id to spread line
            line.write({'move_id': move_id.id})

            created_move_ids.append(move_id.id)

        return created_move_ids

    @api.multi
    def open_move(self):
        """Used by a button to manually view a move from a
        spread line entry."""
        for line in self:
            return {
                'name': _("Journal Entry"),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'domain': [('id', '=', line.move_id.id)],
                }

    @api.multi
    def unlink_move(self):
        """Used by a button to manually unlink a move
        from a spread line entry."""
        for line in self:
            move = line.move_id
            if move.state == 'posted':
                move.button_cancel()
            move.unlink()
            line.move_id = False
        return True

    @api.multi
    def _create_entries(self):
        """Find spread line entries where date is in the past and
        create moves for them."""
        period_obj = self.env['account.period']
        periods = period_obj.with_context(
            account_period_prefer_normal=True).find(
            fields.Date.today()
        )
        period = periods and periods[0] or False
        lines = self.search([('line_date', '<=', period.date_stop),
                             ('move_id', '=', False)])

        result = []

        for line in lines:
            result += line.create_move()

        return result
