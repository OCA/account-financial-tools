# -*- coding: utf-8 -*-
##############################################################################
#
#    Account reversal module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    Copyright (c) 2012-2013 Camptocamp SA (http://www.camptocamp.com)
#    @author Guewen Baconnier
#
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_move_reversal(orm.TransientModel):
    _name = "account.move.reverse"
    _description = "Create reversal of account moves"

    _columns = {
        'date': fields.date(
            'Reversal Date',
            required=True,
            help="Enter the date of the reversal account entries. "
                 "By default, OpenERP proposes the first day of "
                 "the next period."),
        'period_id': fields.many2one(
            'account.period',
            'Reversal Period',
            help="If empty, take the period of the date."),
        'journal_id': fields.many2one(
            'account.journal',
            'Reversal Journal',
            help='If empty, uses the journal of the journal entry '
                 'to be reversed.'),
        'move_prefix': fields.char(
            'Entries Ref. Prefix',
            help="Prefix that will be added to the 'Ref' of the journal "
                 "entry to be reversed to create the 'Ref' of the "
                 "reversal journal entry (no space added after the prefix)."),
        'move_line_prefix': fields.char(
            'Items Name Prefix',
            help="Prefix that will be added to the name of the journal "
                 "item to be reversed to create the name of the reversal "
                 "journal item (a space is added after the prefix)."),
    }

    def _next_period_first_date(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = False
        period_ctx = context.copy()
        period_ctx['account_period_prefer_normal'] = True
        period_obj = self.pool.get('account.period')
        today_period_id = period_obj.find(cr, uid, context=period_ctx)
        if today_period_id:
            today_period = period_obj.browse(
                cr, uid, today_period_id[0], context=context)
            next_period_id = period_obj.next(
                cr, uid, today_period, 1, context=context)
            if next_period_id:
                next_period = period_obj.browse(
                    cr, uid, next_period_id, context=context)
                res = next_period.date_start
        return res

    _defaults = {
        'date': _next_period_first_date,
        'move_line_prefix': 'REV -',
    }

    def action_reverse(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        assert 'active_ids' in context, "active_ids missing in context"

        form = self.read(cr, uid, ids, context=context)[0]

        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        move_obj = self.pool.get('account.move')
        move_ids = context['active_ids']

        period_id = form['period_id'][0] if form.get('period_id') else False
        journal_id = form['journal_id'][0] if form.get('journal_id') else False
        reversed_move_ids = move_obj.create_reversals(
            cr, uid,
            move_ids,
            form['date'],
            reversal_period_id=period_id,
            reversal_journal_id=journal_id,
            move_prefix=form['move_prefix'],
            move_line_prefix=form['move_line_prefix'],
            context=context)

        __, action_id = mod_obj.get_object_reference(
            cr, uid, 'account', 'action_move_journal_line')
        action = act_obj.read(cr, uid, [action_id], context=context)[0]
        action['domain'] = unicode([('id', 'in', reversed_move_ids)])
        action['name'] = _('Reversal Entries')
        action['context'] = unicode({'search_default_to_be_reversed': 0})
        return action
