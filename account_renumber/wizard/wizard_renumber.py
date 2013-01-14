# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account renumber wizard
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

"""
Account renumber wizard
"""
__author__ = ["Borja López Soilán (Pexego)",
                "Omar Castiñeira Saavedra (Pexego)"]


from osv import osv, fields
import logging
from tools.translate import _
import time
from datetime import datetime


class wizard_renumber(osv.osv_memory):
    """
    Account renumber wizard.
    """

    _name = "wizard.renumber"

    _columns = {
        'journal_ids': fields.many2many('account.journal',
                                        'account_journal_wzd_renumber_rel', 'wizard_id',
                                        'journal_id', required=True, help="Journals to renumber",
                                        string="Journals"),
        'period_ids': fields.many2many('account.period',
                                       'account_period_wzd_renumber_rel', 'wizard_id',
                                       'period_id', required=True,
                                       help='Fiscal periods to renumber', string="Periods"),
        'number_next': fields.integer('First Number', required=True,
                                      help="Journal sequences will start counting on this number"),
        'state': fields.selection([('init', 'Initial'), ('renumber', 'Renumbering')],
                                  readonly=True)
    }

    _defaults = {
        'number_next': 1,
        'state': 'init'
    }

    ############################################################################
    # Helper methods
    ##########################################################################

    def _process(self, s, date_to_use=None):
        """
        Based on ir_sequence._process. We need to have our own method
        as ir_sequence one will always use the current date.
        We will use the given date instead.
        """
        date_to_use = date_to_use or time
        return (s or '') % {
            'year': date_to_use.strftime('%Y'),
            'month': date_to_use.strftime('%m'),
            'day': date_to_use.strftime('%d'),
            'y': date_to_use.strftime('%y'),
            'doy': date_to_use.strftime('%j'),
            'woy': date_to_use.strftime('%W'),
            'weekday': date_to_use.strftime('%w'),
            'h24': time.strftime('%H'),
            'h12': time.strftime('%I'),
            'min': time.strftime('%M'),
            'sec': time.strftime('%S'),
        }

    def get_id(self, cr, uid, sequence_id, test='id=%s', context=None, date_to_use=None):
        """
        Based on ir_sequence.get_id. We need to have our own method
        as ir_sequence one will always use the current date for the prefix
        and sufix processing. We will use the given date instead.
        """
        try:
            cr.execute('SELECT id, number_next, prefix, suffix, padding FROM ir_sequence WHERE ' + test + ' AND active=%s FOR UPDATE', (sequence_id, True))
            res = cr.dictfetchone()
            if res:
                cr.execute('UPDATE ir_sequence SET number_next=number_next+number_increment WHERE id=%s AND active=%s', (res['id'], True))
                if res['number_next']:
                    return self._process(res['prefix'], date_to_use=date_to_use) + '%%0%sd' % res['padding'] % res['number_next'] + self._process(res['suffix'], date_to_use=date_to_use)
                else:
                    return self._process(res['prefix'], date_to_use=date_to_use) + self._process(res['suffix'], date_to_use=date_to_use)
        finally:
            cr.commit()
        return False

    def get_sequence_id_for_fiscalyear_id(self, cr, uid, sequence_id, fiscalyear_id, context=None):
        """
        Based on ir_sequence.get_id from the account module.
        Allows us to get the real sequence for the given fiscal year.
        """
        cr.execute('SELECT id FROM ir_sequence WHERE id=%s AND active=%s',
                   (sequence_id, True,))
        res = cr.dictfetchone()
        if res:
            seq_facade = self.pool.get('ir.sequence')
            for line in seq_facade.browse(cr, uid, res['id'], context=context).fiscal_ids:
                if line.fiscalyear_id.id == fiscalyear_id:
                    return line.sequence_id.id
        return sequence_id

    ############################################################################
    # Renumber form/action
    ##########################################################################

    def renumber(self, cr, uid, ids, context):
        """
        Action that renumbers all the posted moves on the given
        journal and periods, and returns their ids.
        """
        logger = logging.getLogger("account_renumber")
        obj = self.browse(cr, uid, ids[0])

        period_ids = [x.id for x in obj.period_ids]
        journal_ids = [x.id for x in obj.journal_ids]
        number_next = obj.number_next or 1

        if not (period_ids and journal_ids):
            raise osv.except_osv(_('No Data Available'), _(
                'No records found for your selection!'))

        logger.debug("Searching for account moves to renumber.")

        move_facade = self.pool.get('account.move')
        move_ids = move_facade.search(cr, uid, [('journal_id', 'in', journal_ids), ('period_id', 'in', period_ids), ('state', '=', 'posted')], limit=0, order='date,id', context=context)

        if len(move_ids) == 0:
            raise osv.except_osv(_('No Data Available'), _(
                'No records found for your selection!'))

        sequences_seen = []

        logger.debug("Renumbering %d account moves." % len(move_ids))

        for move in move_facade.browse(cr, uid, move_ids):
            #
            # Get the sequence to use for this move.
            # Note: We will use the journal's sequence or one of its
            #       children (if it has children sequences per fiscalyear)
            #
            sequence_id = self.get_sequence_id_for_fiscalyear_id(cr, uid,
                                                                 sequence_id=move.journal_id.sequence_id.id,
                                                                 fiscalyear_id=move.period_id.fiscalyear_id.id)
            if not sequence_id in sequences_seen:
                # First time we see this sequence, reset it
                self.pool.get('ir.sequence').write(
                    cr, uid, [sequence_id], {'number_next': number_next})
                sequences_seen.append(sequence_id)

            #
            # Generate (using our own get_id) and write the new move number.
            #
            date_to_use = datetime.strptime(move.date, '%Y-%m-%d')
            new_name = self.get_id(cr, uid, sequence_id,
                                   context=context, date_to_use=date_to_use)
            # Note: We can't just do a
            # "move_facade.write(cr, uid, [move.id], {'name': new_name})"
            # cause it might raise a "You can't do this modification on a confirmed entry"
            # exception.
            cr.execute('UPDATE account_move SET name=%s WHERE id=%s',
                       (new_name, move.id))

        logger.debug("%d account moves renumbered." % len(move_ids))

        obj.write({'state': 'renumber'})

        return True

    ############################################################################
    # Show results action
    ##########################################################################
    def show_results(self, cr, uid, ids, context):
        """
        Action that shows the list of (non-draft) account moves from
        the selected journals and periods, so the user can review
        the renumbered account moves.
        """
        obj = self.browse(cr, uid, ids[0])
        period_ids = [x.id for x in obj.period_ids]
        journal_ids = [x.id for x in obj.journal_ids]

        assert (period_ids and journal_ids)

        cr.execute('select id,name from ir_ui_view where model=%s and type=%s',
                   ('account.move', 'tree'))
        view_res = cr.fetchone()
        res = {
            'domain': "[('journal_id','in',%s), ('period_id','in',%s), ('state','=','posted')]" % (repr(journal_ids), repr(period_ids)),
            'name': _("Renumbered account moves"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': view_res,
            'context': context,
            'type': 'ir.actions.act_window',
        }
        return res

wizard_renumber()
