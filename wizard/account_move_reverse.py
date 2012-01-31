# -*- coding: utf-8 -*-
##############################################################################
#
#    Account reversal module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    Copyright (c) 2012 Camptocamp SA (http://www.camptocamp.com)
#    @author Guewen Baconnier
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################



from osv import osv, fields
from tools.translate import _


class account_move_reversal(osv.osv_memory):
    _name = "account.move.reverse"
    _description = "Create reversal of account moves"

    _columns = {
        'date': fields.date('Reversal Date', required=True, help="Enter the date of the reversal account entries. By default, OpenERP proposes the first day of the next period."),
        'period_id': fields.many2one('account.period', 'Reversal Period', help="If empty, take the period of the date."),
        'journal_id': fields.many2one('account.journal', 'Reversal Journal', help='If empty, uses the journal of the journal entry to be reversed.'),
        'move_prefix': fields.char('Entries Ref. Prefix', size=32, help="Prefix that will be added to the 'Ref' of the journal entry to be reversed to create the 'Ref' of the reversal journal entry (no space added after the prefix)."),
        'move_line_prefix': fields.char('Items Name Prefix', size=32, help="Prefix that will be added to the name of the journal item to be reversed to create the name of the reversal journal item (a space is added after the prefix)."),
        }

    def _next_period_first_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        period_obj = self.pool.get('account.period')
        current_period_id = period_obj.find(cr, uid, context=context)[0]
        current_period = period_obj.browse(cr, uid, current_period_id, context=context)
        next_period_id = period_obj.next(cr, uid, current_period, 1, context=context)
        next_period = period_obj.browse(cr, uid, next_period_id, context=context)
        return next_period.date_start

    _defaults = {
        'date': _next_period_first_date,
        'move_line_prefix': lambda *a: 'REV -',
        }

    def action_reverse(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        form = self.read(cr, uid, ids, context=context)[0]

        action = {'type': 'ir.actions.act_window_close'}

        if context.get('active_ids', False):
            mod_obj = self.pool.get('ir.model.data')
            act_obj = self.pool.get('ir.actions.act_window')
            move_obj = self.pool.get('account.move')
            move_ids = context['active_ids']

            period_id = form.get('period_id', False) and form['period_id'][0] or False
            journal_id = form.get('journal_id', False) and form['journal_id'][0] or False
            reversed_move_ids = move_obj.create_reversals(
                cr, uid,
                move_ids,
                form['date'],
                reversal_period_id=period_id,
                reversal_journal_id=journal_id,
                move_prefix=form['move_prefix'],
                move_line_prefix=form['move_line_prefix'],
                context=context)

            action_ref = mod_obj.get_object_reference(cr, uid, 'account', 'action_move_journal_line')
            action_id = action_ref and action_ref[1] or False
            action = act_obj.read(cr, uid, [action_id], context=context)[0]
            action['domain'] = str([('id', 'in', reversed_move_ids)])
            action['name'] = _('Reversal Entries')
            action['context'] = unicode({'search_default_to_be_reversed': 0})
        return action

account_move_reversal()
