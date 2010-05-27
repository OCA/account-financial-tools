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
Revalidate Account Moves Wizard
"""
__author__ = "Borja López Soilán (Pexego)"

import re
from osv import fields,osv
from tools.translate import _

class pxgo_revalidate_moves(osv.osv_memory):
    """
    Revalidate Account Moves Wizard

    Revalidates all the (already confirmed) moves, so their analytic lines
    are recomputed (to fix the data after problems like this:
    https://bugs.launchpad.net/openobject-addons/+bug/582988).
    """
    _name = "pxgo_account_admin_tools.pxgo_revalidate_moves"
    _description = "Revalidate Account Moves Wizard"

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        'period_ids': fields.many2many('account.period', 'pxgo_revalidate_moves_period_rel', 'wizard_id', 'period_id', "Periods"),
        'move_ids': fields.many2many('account.move', 'pxgo_revalidate_moves_moves_rel', 'wizard_id', 'move_id', 'Moves'),
        'state': fields.selection([('new','New'), ('ready', 'Ready'), ('done','Done')], 'Status', readonly=True),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        'move_ids': lambda self, cr, uid, context: context and context.get('move_ids', None),
        'period_ids': lambda self, cr, uid, context: context and context.get('period_ids', None),
        'state': lambda self, cr, uid, context: context and context.get('state', 'new'),
    }


    def _next_view(self, cr, uid, ids, view_name, args=None, context=None):
        """
        Return the next view
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
            'name': _("Revalidate Moves"),
            'type': 'ir.actions.act_window',
            'res_model': 'pxgo_account_admin_tools.pxgo_revalidate_moves',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(resource_id, 'form')],
            'domain': "[('id', 'in', %s)]" % ids,
            'context': ctx,
            'target': 'new',
        }


    def action_skip_new(self, cr, uid, ids, context=None):
        """
        Action that just skips the to the ready state
        """
        return self._next_view(cr, uid, ids, 'view_pxgo_revalidate_moves_ready_form', {'state': 'ready'}, context)


    def action_find_moves_missing_analytic_lines(self, cr, uid, ids, context=None):
        """
        Finds account moves with missing analytic lines and adds them
        to the move_ids many2many field.
        """
        wiz = self.browse(cr, uid, ids[0], context)

        # FIXME: The next block of code is a workaround to the lp:586252 bug of the 6.0 client.
        #        (https://bugs.launchpad.net/openobject-client/+bug/586252)
        if wiz.period_ids:
            period_ids = [period.id for period in wiz.period_ids]
        else:
            period_ids = context and context.get('period_ids')

        query = """
                SELECT account_move_line.move_id FROM account_move_line
                LEFT JOIN account_analytic_line
                ON account_analytic_line.move_id = account_move_line.id
                WHERE account_move_line.analytic_account_id IS NOT NULL AND account_analytic_line.id IS NULL
                """
        if period_ids:
            query += """      AND period_id IN %s"""
            cr.execute(query, (tuple(period_ids),))
        else:
            cr.execute(query)

        move_ids = filter(None, map(lambda x:x[0], cr.fetchall()))

        #
        # Return the next view: Show 'ready' view
        #
        args = {
            'move_ids': move_ids,
            'state': 'ready',
        }
        return self._next_view(cr, uid, ids, 'view_pxgo_revalidate_moves_ready_form', args, context)


    def action_revalidate_moves(self, cr, uid, ids, context=None):
        """
        Calls the validate method of the account moves for each move in the
        move_ids many2many.
        """
        wiz = self.browse(cr, uid, ids[0], context)

        # FIXME: The next block of code is a workaround to the lp:586252 bug of the 6.0 client.
        #        (https://bugs.launchpad.net/openobject-client/+bug/586252)
        if wiz.move_ids:
            move_ids = [line.id for line in wiz.move_ids]
        else:
            move_ids = context and context.get('move_ids')

        for move in self.pool.get('account.move').browse(cr, uid, move_ids, context=context):
            # We validate the moves one by one to prevent problems
            self.pool.get('account.move').validate(cr, uid, [move.id], context)
        
        #
        # Return the next view: Show 'done' view
        #
        args = {
            'move_ids': move_ids,
            'state': 'done',
        }
        return self._next_view(cr, uid, ids, 'view_pxgo_revalidate_moves_done_form', args, context)


pxgo_revalidate_moves()


