# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2011 Nicolas Bessi (Camptocamp)
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _


class AccountMove(models.Model):
    _inherit = "account.move"

    to_be_reversed = fields.Boolean(
        string="To Be Reversed",
        copy=False,
        help="Check this box if your entry has to be reversed at the end "
             "of period.")
    reversal_id = fields.Many2one(
        comodel_name='account.move', ondelete='set null', readonly=True,
        string="Reversal Entry")

    @api.model
    def _move_lines_reverse_prepare(self, move, date=False, journal=False,
                                    line_prefix=False):
        for line in move.get('line_ids', []):
            date = date or line[2].get('date', self.date)
            if not journal:
                journal = self.journal_id
            journal_id = journal and journal.id
            journal_id = journal_id or line[2].get('journal_id', False)
            name = line[2].get('name', False) or line_prefix
            debit = line[2].get('debit', 0.)
            credit = line[2].get('credit', 0.)
            amount_currency = line[2].get('amount_currency', 0.)
            if line_prefix and line_prefix != name:
                name = ' '.join([line_prefix, name])
            line[2].update({
                'name': name,
                'date': date,
                'journal_id': journal_id,
                'debit': credit,
                'credit': debit,
                'amount_currency': -amount_currency,
            })
        return move

    @api.model
    def _move_reverse_prepare(self, date=False, journal=False,
                              move_prefix=False):
        self.ensure_one()
        journal = journal or self.journal_id
        if journal.company_id != self.company_id:
            raise UserError(
                _("Wrong company Journal is '%s' but we have '%s'") % (
                    journal.company_id.name, self.company_id.name))
        ref = self.ref or move_prefix
        if move_prefix and move_prefix != ref:
            ref = ' '.join([move_prefix, ref])
        date = date or self.date
        move = self.copy_data()[0]
        move.update({
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
            'to_be_reversed': False,
            'state': 'draft',
        })
        return move

    @api.multi
    def move_reverse_reconcile(self):
        for move in self.filtered('reversal_id'):
            rec = {}
            lines = move.reversal_id.line_ids.filtered('account_id.reconcile')
            for line in lines:
                rec.setdefault((line.account_id, line.partner_id),
                               self.env['account.move.line'])
                rec[(line.account_id, line.partner_id)] += line
            lines = move.line_ids.filtered('account_id.reconcile')
            for line in lines:
                rec[(line.account_id, line.partner_id)] += line
            for lines in list(rec.values()):
                lines.reconcile()
        return True

    @api.multi
    def create_reversals(self, date=False, journal=False, move_prefix=False,
                         line_prefix=False, reconcile=False):
        """
        Create the reversal of one or multiple moves

        :param self: moves to reverse
        :param date: when the reversal must be input
                     (use original if empty)
        :param journal: journal on which create the move
                        (use original if empty)
        :param move_prefix: prefix for the move's name
        :param line_prefix: prefix for the move line's names
        :param reconcile: reconcile lines (if account with reconcile = True)

        :return: Returns a recordset of the created reversal moves
        """
        moves = self.env['account.move']
        for orig in self:
            data = orig._move_reverse_prepare(
                date=date, journal=journal, move_prefix=move_prefix)
            data = orig._move_lines_reverse_prepare(
                data, date=date, journal=journal, line_prefix=line_prefix)
            reversal_move = self.create(data)
            moves |= reversal_move
            orig.write({
                'reversal_id': reversal_move.id,
                'to_be_reversed': False,
            })
        if moves:
            moves._post_validate()
            moves.post()
            if reconcile:
                self.move_reverse_reconcile()
        return moves
