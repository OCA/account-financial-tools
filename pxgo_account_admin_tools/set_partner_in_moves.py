# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
Set Partner in Moves Wizard
"""
__author__ = "Borja López Soilán (Pexego)"

import re
from osv import fields,osv
from tools.translate import _

class pxgo_set_partner_in_moves(osv.osv_memory):
    """
    Set Partner in Moves Wizard

    Searchs for account move lines of that use the payable/receivable account
    of a single partner, and have no partner reference in the line,
    and sets the partner reference (partner_id).
    This may fix cases where the receivable/payable amounts displayed in the
    partner form does not match the balance of the receivable/payable accounts.
    """
    _name = "pxgo_account_admin_tools.pxgo_set_partner_in_moves"
    _description = "Move Partner Account Wizard"

    _columns = {
        'state': fields.selection([('new','New'), ('ready', 'Ready'), ('done','Done')], 'Status', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        'period_ids': fields.many2many('account.period', 'pxgo_set_partner_in_moves_period_rel', 'wizard_id', 'period_id', "Periods"),
        'move_line_ids': fields.many2many('account.move.line', 'pxgo_set_partner_in_move_move_line_rel', 'wizard_id', 'line_id', 'Move Lines'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        'move_line_ids': lambda self, cr, uid, context: context and context.get('move_line_ids', None),
        'period_ids': lambda self, cr, uid, context: context and context.get('period_ids', None),
        'state': lambda self, cr, uid, context: context and context.get('state', 'new'),
    }


    def _next_view(self, cr, uid, ids, view_name, args=None, context=None):
        """
        Return the next wizard view
        """
        if context is None:
            context = {}
        if args is None:
            args = {}
        ctx = context.copy()
        ctx.update(args)

        model_data_ids = self.pool.get('ir.model.data').search(cr, uid, [
                    ('model', '=', 'ir.ui.view'),
                    ('module', '=', 'pxgo_account_admin_tools'),
                    ('name', '=', view_name)
                ])
        resource_id = self.pool.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _("Set Partner Reference in Moves"),
            'type': 'ir.actions.act_window',
            'res_model': 'pxgo_account_admin_tools.pxgo_set_partner_in_moves',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(resource_id, 'form')],
            'domain': "[('id', 'in', %s)]" % ids,
            'context': ctx,
            'target': 'new',
        }


    def _get_accounts_map(self, cr, uid, context=None):
        """
        Find the receivable/payable accounts that are associated with
        a single partner and return a (account.id, partner.id) map
        """
        partner_ids = self.pool.get('res.partner').search(cr, uid, [], context=context)
        accounts_map = {}
        for partner in self.pool.get('res.partner').browse(cr, uid, partner_ids, context=context):
            #
            # Add the receivable account to the map
            #
            if accounts_map.get(partner.property_account_receivable.id, None) is None:
                accounts_map[partner.property_account_receivable.id] = partner.id
            else:
                # Two partners with the same receivable account: ignore
                # this account!
                accounts_map[partner.property_account_receivable.id] = 0
            #
            # Add the payable account to the map
            #
            if accounts_map.get(partner.property_account_payable.id, None) is None:
                accounts_map[partner.property_account_payable.id] = partner.id
            else:
                # Two partners with the same receivable account: ignore
                # this account!
                accounts_map[partner.property_account_payable.id] = 0
        return accounts_map


    def action_skip_new(self, cr, uid, ids, context=None):
        """
        Action that just skips the to the ready state
        """
        return self._next_view(cr, uid, ids, 'view_pxgo_set_partner_in_moves_ready_form', {'state': 'ready'}, context)


    def action_find_moves_missing_partner(self, cr, uid, ids, context=None):
        """
        Action that searchs for account move lines of payable/receivable
        accounts (of just one partner) that don't have the partner reference.
        """
        wiz = self.browse(cr, uid, ids[0], context)

        # FIXME: The next block of code is a workaround to the lp:586252 bug of the 6.0 client.
        #        (https://bugs.launchpad.net/openobject-client/+bug/586252)
        if wiz.period_ids:
            period_ids = [period.id for period in wiz.period_ids]
        else:
            period_ids = context and context.get('period_ids')

        move_line_ids = []
        accounts_map = self._get_accounts_map(cr, uid, context=context)

        #
        # Find the account move lines, of each of the accounts in the map
        # that don't have a partner set.
        #
        query = """
                SELECT id FROM account_move_line
                WHERE account_id=%s
                      AND partner_id IS NULL
                """
        if period_ids:
            query += """      AND period_id IN %s"""

        for account_id in accounts_map.keys():
            if accounts_map[account_id] != 0:
                if period_ids:
                    cr.execute(query, (account_id, tuple(period_ids)))
                else:
                    cr.execute(query, (account_id,))
                new_move_line_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
                if new_move_line_ids:
                    move_line_ids.extend(new_move_line_ids)

        #
        # Return the next view: Show 'ready' view
        #
        args = {
            'move_line_ids': move_line_ids,
            'state': 'ready',
        }
        return self._next_view(cr, uid, ids, 'view_pxgo_set_partner_in_moves_ready_form', args, context)



    def action_set_partner_in_moves(self, cr, uid, ids, context=None):
        """
        Action that sets for each partner payable/receivable account,
        that is used only on one partner, the parner reference on its move
        lines.
        """
        wiz = self.browse(cr, uid, ids[0], context)

        # FIXME: The next block of code is a workaround to the lp:586252 bug of the 6.0 client.
        #        (https://bugs.launchpad.net/openobject-client/+bug/586252)
        if wiz.move_line_ids:
            move_line_ids = [line.id for line in wiz.move_line_ids]
        else:
            move_line_ids = context and context.get('move_line_ids')

        accounts_map = self._get_accounts_map(cr, uid, context=context)

        #
        # Update the account move lines, of each of the accounts in the map
        # that don't have a partner set, with the associated partner.
        #
        query = """
                UPDATE account_move_line
                SET partner_id=%s
                WHERE id=%s
                      AND partner_id IS NULL
                """
        for line in self.pool.get('account.move.line').browse(cr, uid, move_line_ids, context=context):
            if accounts_map[line.account_id.id] != 0:
                cr.execute(query, (accounts_map[line.account_id.id], line.id))

        #
        # Return the next view: Show 'done' view
        #
        args = {
            'move_line_ids': move_line_ids,
            'state': 'done',
        }
        return self._next_view(cr, uid, ids, 'view_pxgo_set_partner_in_moves_done_form', args, context)


pxgo_set_partner_in_moves()


