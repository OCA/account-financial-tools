# -*- coding: utf-8 -*-
# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2011 Nicolas Bessi (Camptocamp)
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _
from openerp.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    to_be_reversed = fields.Boolean(
        string="To Be Reversed",
        help="Check this box if your entry has to be reversed at the end "
             "of period.")
    reversal_id = fields.Many2one(
        comodel_name='account.move', ondelete='set null', readonly=True,
        string="Reversal Entry")

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
            for lines in rec.itervalues():
                lines.reconcile()
        return True

    @api.multi
    def _reverse_move(self, date=None, journal_id=None):
        reversal_move = super(AccountMove, self)._reverse_move(
            date=date,
            journal_id=journal_id)

        self.write({
            'reversal_id': reversal_move.id,
            'to_be_reversed': False,
        })
        return reversal_move

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
        self.reverse_moves(date=date, journal_id=journal)
        moves = self.mapped('reversal_id')
        if move_prefix or line_prefix:
            for orig in self:
                ref = orig.name or move_prefix
                if move_prefix and move_prefix != ref:
                    ref = ' '.join([move_prefix, ref])
                    orig.reversal_id.write({'ref': ref})
                if line_prefix:
                    for line in orig.reversal_id.line_ids:
                        if line.name and line_prefix != line.name:
                            name = ' '.join([line_prefix, line.name])
                            line.write({'name': name})

        if moves:
            if reconcile:
                self.move_reverse_reconcile()
        return moves
