# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Agile Business Group sagl
#    (<http://www.agilebg.com>)
#    @authors Lorenzo Battistini <lorenzo.battistini@agilebg.com>
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


class AccountReopenReconciliation(orm.TransientModel):

    _name = 'account.reopen.reconciliation'
    _columns = {
        'counterpart_account_id': fields.many2one(
            'account.account', 'Counterpart',
            help="Usually, a liquidity account", required=True),
        'date': fields.date('Reopening entry date', required=True),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True),
        }
    _defaults = {
        'date': fields.date.context_today,
        }

    def reopen(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        move_line_obj = self.pool['account.move.line']
        move_obj = self.pool['account.move']
        mod_obj = self.pool['ir.model.data']
        act_obj = self.pool['ir.actions.act_window']
        active_ids = context.get('active_ids')
        if not active_ids:
            raise orm.except_orm(_('Error'), _('No journal item selected'))
        move_ids = []
        for active_id in active_ids:
            move_line = move_line_obj.browse(
                cr, uid, active_ids[0], context=context)
            if (
                not move_line.reconcile_id
                and not move_line.reconcile_partial_id
            ):
                raise orm.except_orm(
                    _("Error"), _("The item is not reconciled"))
            other_partner_line = False
            if move_line.reconcile_id:
                if len(move_line.reconcile_id.line_id) > 2:
                    raise orm.except_orm(
                        _('Error'),
                        _("Can't reopen reconciliations with more than "
                          "2 items"))
                for line in move_line.reconcile_id.line_id:
                    if line.id != move_line.id:
                        other_partner_line = line
            elif move_line.reconcile_partial_id:
                if len(move_line.reconcile_partial_id.line_partial_ids) > 2:
                    raise orm.except_orm(
                        _('Error'),
                        _("Can't reopen reconciliations with more than "
                          "2 items"))
                for line in move_line.reconcile_partial_id.line_partial_ids:
                    if line.id != move_line.id:
                        other_partner_line = line
            move_line._remove_move_reconcile(context=context)
            wizard = self.browse(cr, uid, ids[0], context=context)
            move_id = move_obj.create(cr, uid, {
                'date': wizard.date,
                'journal_id': wizard.journal_id.id,
                }, context=context)
            partner_line_vals = {
                'name': _("Reopening %s") % move_line.name,
                'account_id': move_line.account_id.id,
                'move_id': move_id,
                'partner_id': move_line.partner_id.id,
                }
            if other_partner_line.debit:
                partner_line_vals['credit'] = other_partner_line.debit
            elif other_partner_line.credit:
                partner_line_vals['debit'] = other_partner_line.credit
            counterpart_line_vals = {
                'name': _("Counterpart - Reopening %s") % move_line.name,
                'account_id': wizard.counterpart_account_id.id,
                'move_id': move_id,
                }
            if other_partner_line.debit:
                counterpart_line_vals['debit'] = other_partner_line.debit
            elif other_partner_line.credit:
                counterpart_line_vals['credit'] = other_partner_line.credit
            partner_line_id = move_line_obj.create(
                cr, uid, partner_line_vals, context=context)
            move_line_obj.create(
                cr, uid, counterpart_line_vals, context=context)
            move_line_obj.reconcile_partial(
                cr, uid, [
                    partner_line_id, other_partner_line.id
                    ], context=context)
            move_line.write({
                'reopening_line_ids': [(4, partner_line_id)],
                }, context=context)
            move_ids.append(move_id)

        __, action_id = mod_obj.get_object_reference(
            cr, uid, 'account', 'action_move_journal_line')
        action = act_obj.read(cr, uid, [action_id], context=context)[0]
        action['domain'] = unicode([('id', 'in', move_ids)])
        return action
