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
from openerp.osv import fields, orm
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import logging

_logger = logging.getLogger(__name__)


class wizard_renumber(orm.TransientModel):
    _name = "wizard.renumber"
    _description = "Account renumber wizard"
    _columns = {
        'journal_ids': fields.many2many('account.journal',
                                        'account_journal_wzd_renumber_rel',
                                        'wizard_id', 'journal_id',
                                        required=True,
                                        help="Journals to renumber",
                                        string="Journals"),
        'period_ids': fields.many2many('account.period',
                                       'account_period_wzd_renumber_rel',
                                       'wizard_id', 'period_id',
                                       required=True,
                                       help='Fiscal periods to renumber',
                                       string="Periods", ondelete='null'),
        'number_next': fields.integer('First Number', required=True,
                                      help="Journal sequences will start "
                                           "counting on this number"),
        'state': fields.selection([('init', 'Initial'),
                                   ('renumber', 'Renumbering')], readonly=True)
    }

    _defaults = {
        'number_next': 1,
        'state': 'init'
    }

    ###############################
    # Helper methods
    ###############################

    def get_sequence_id_for_fiscalyear_id(self, cr, uid, sequence_id,
                                          fiscalyear_id, context=None):
        """
        Based on ir_sequence.get_id from the account module.
        Allows us to get the real sequence for the given fiscal year.
        """
        sequence = self.pool['ir.sequence'].browse(cr, uid, sequence_id,
                                                   context=context)
        for line in sequence.fiscal_ids:
            if line.fiscalyear_id.id == fiscalyear_id:
                return line.sequence_id.id
        return sequence_id

    ##########################################################################
    # Renumber form/action
    ##########################################################################

    def renumber(self, cr, uid, ids, context=None):
        """
        Action that renumbers all the posted moves on the given
        journal and periods, and returns their ids.
        """
        form = self.browse(cr, uid, ids[0], context=context)
        period_ids = [x.id for x in form.period_ids]
        journal_ids = [x.id for x in form.journal_ids]
        number_next = form.number_next or 1
        if not (period_ids and journal_ids):
            raise orm.except_orm(_('No Data Available'),
                                 _('No records found for your selection!'))
        _logger.debug("Searching for account moves to renumber.")
        move_obj = self.pool['account.move']
        sequence_obj = self.pool['ir.sequence']
        sequences_seen = []
        for period in period_ids:
            move_ids = move_obj.search(cr, uid,
                                       [('journal_id', 'in', journal_ids),
                                        ('period_id', '=', period),
                                        ('state', '=', 'posted')],
                                       limit=0, order='date,id',
                                       context=context)
            if not move_ids:
                continue
            _logger.debug("Renumbering %d account moves.", len(move_ids))
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                sequence_id = self.get_sequence_id_for_fiscalyear_id(
                    cr, uid,
                    sequence_id=move.journal_id.sequence_id.id,
                    fiscalyear_id=move.period_id.fiscalyear_id.id
                )
                if sequence_id not in sequences_seen:
                    sequence_obj.write(cr, SUPERUSER_ID, [sequence_id],
                                       {'number_next': number_next})
                    sequences_seen.append(sequence_id)
                # Generate (using our own get_id) and write the new move number
                c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                new_name = sequence_obj.next_by_id(
                    cr, uid,
                    move.journal_id.sequence_id.id,
                    context=c
                )
                # Note: We can't just do a
                # "move_obj.write(cr, uid, [move.id], {'name': new_name})"
                # cause it might raise a
                # ``You can't do this modification on a confirmed entry``
                # exception.
                cr.execute('UPDATE account_move SET name=%s WHERE id=%s',
                           (new_name, move.id))
            _logger.debug("%d account moves renumbered.", len(move_ids))
        sequences_seen = []
        form.write({'state': 'renumber'})
        data_obj = self.pool['ir.model.data']
        view_ref = data_obj.get_object_reference(cr, uid, 'account',
                                                 'view_move_tree')
        view_id = view_ref and view_ref[1] or False,
        res = {
            'type': 'ir.actions.act_window',
            'name': _("Renumbered account moves"),
            'res_model': 'account.move',
            'domain': ("[('journal_id','in',%s), ('period_id','in',%s), "
                       "('state','=','posted')]"
                       % (journal_ids, period_ids)),
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': view_id,
            'context': context,
            'target': 'current',
        }
        return res
