# -*- coding: utf-8 -*-
##############################################################################
#
#    Account reversal module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    with the kind advice of Nicolas Bessi from Camptocamp
#    Copyright (C) 2012-2013 Camptocamp SA (http://www.camptocamp.com)
#    @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class account_move(orm.Model):
    _inherit = "account.move"

    _columns = {
        'to_be_reversed': fields.boolean(
            'To Be Reversed',
            help='Check this box if your entry has to be'
                 'reversed at the end of period.'),
        'reversal_id': fields.many2one(
            'account.move',
            'Reversal Entry',
            ondelete='set null',
            readonly=True),
        }

    def _move_reversal(self, cr, uid, move, reversal_date,
                       reversal_period_id=False, reversal_journal_id=False,
                       move_prefix=False, move_line_prefix=False,
                       context=None):
        """
        Create the reversal of a move

        :param move: browse instance of the move to reverse
        :param reversal_date: when the reversal must be input
        :param reversal_period_id: facultative period to write on the move
                                   (use the period of the date if empty
        :param reversal_journal_id: facultative journal on which create
                                    the move
        :param move_prefix: prefix for the move's name
        :param move_line_prefix: prefix for the move line's names

        :return: Returns the id of the created reversal move
        """
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        period_ctx = context.copy()
        period_ctx['company_id'] = move.company_id.id

        if not reversal_period_id:
            reversal_period_id = period_obj.find(
                    cr, uid, reversal_date, context=period_ctx)[0]
        if not reversal_journal_id:
            reversal_journal_id = move.journal_id.id

        reversal_ref = ''.join([x for x in [move_prefix, move.ref] if x])
        reversal_move_id = self.copy(cr, uid, move.id,
                                     default={
                                         'date': reversal_date,
                                         'period_id': reversal_period_id,
                                         'ref': reversal_ref,
                                         'journal_id': reversal_journal_id,
                                         'to_be_reversed': False,
                                     },
                                     context=context)

        self.write(cr, uid, [move.id],
                   {'reversal_id': reversal_move_id,
                    # ensure to_be_reversed is true if ever it was not
                    'to_be_reversed': True},
                   context=context)

        reversal_move = self.browse(cr, uid, reversal_move_id, context=context)
        for reversal_move_line in reversal_move.line_id:
            reversal_ml_name = ' '.join(
                    [x for x
                        in [move_line_prefix, reversal_move_line.name]
                        if x])
            move_line_obj.write(
                cr,
                uid,
                [reversal_move_line.id],
                {'debit': reversal_move_line.credit,
                 'credit': reversal_move_line.debit,
                 'amount_currency': reversal_move_line.amount_currency * -1,
                 'name': reversal_ml_name},
                context=context,
                check=True,
                update_check=True)

        self.validate(cr, uid, [reversal_move_id], context=context)
        return reversal_move_id

    def create_reversals(self, cr, uid, ids, reversal_date,
                         reversal_period_id=False, reversal_journal_id=False,
                         move_prefix=False, move_line_prefix=False,
                         context=None):
        """
        Create the reversal of one or multiple moves

        :param reversal_date: when the reversal must be input
        :param reversal_period_id: facultative period to write on the move
                                   (use the period of the date if empty
        :param reversal_journal_id: facultative journal on which create
                                    the move
        :param move_prefix: prefix for the move's name
        :param move_line_prefix: prefix for the move line's names

        :return: Returns a list of ids of the created reversal moves
        """
        if isinstance(ids, (int, long)):
            ids = [ids]

        reversed_move_ids = []
        for src_move in self.browse(cr, uid, ids, context=context):
            if src_move.reversal_id:
                continue  # skip the reversal creation if already done

            reversal_move_id = self._move_reversal(
                    cr, uid,
                    src_move,
                    reversal_date,
                    reversal_period_id=reversal_period_id,
                    reversal_journal_id=reversal_journal_id,
                    move_prefix=move_prefix,
                    move_line_prefix=move_line_prefix,
                    context=context)

            if reversal_move_id:
                reversed_move_ids.append(reversal_move_id)

        return reversed_move_ids
