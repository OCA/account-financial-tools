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

class pxgo_revalidate_moves_wizard(osv.osv_memory):
    """
    Revalidate Account Moves Wizard

    Revalidates all the (already confirmed) moves, so their analytic lines
    are recomputed (to fix the data after problems like this:
    https://bugs.launchpad.net/openobject-addons/+bug/582988).
    """
    _name = "pxgo_revalidate_moves_wizard"
    _description = "Revalidate Account Moves Wizard"

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        'period_ids': fields.many2many('account.period', 'pxgo_revalidate_moves_wizard_period_rel', 'wizard_id', 'period_id', "Periods"),
        'move_ids': fields.many2many('account.move', 'pxgo_revalidate_moves_wizard_moves_rel', 'wizard_id', 'move_id', 'Moves'),
        'state': fields.selection([('new','New'), ('ready', 'Ready'), ('done','Done')], 'Status', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'new',
    }

    def action_skip_new(self, cr, uid, ids, context=None):
        """
        Skips to the ready state.
        """
        for wiz in self.browse(cr, uid, ids, context):
            self.write(cr, uid, [wiz.id], { 'state': 'ready' })
        return True

    def action_find_moves_missing_analytic_lines(self, cr, uid, ids, context=None):
        """
        Finds account moves with missing analytic lines and adds them
        to the move_ids many2many field.
        """
        for wiz in self.browse(cr, uid, ids, context):
            period_ids = [period.id for period in wiz.period_ids]
            query = """
                    SELECT account_move_line.move_id FROM account_move_line
                    LEFT JOIN account_analytic_line
                    ON account_analytic_line.move_id = account_move_line.id
                    WHERE account_move_line.analytic_account_id IS NOT NULL AND account_analytic_line.id IS NULL
                    """
            periods_str = ','.join(map(str, period_ids))
            if period_ids:
                query += """      AND period_id IN (%s)""" % periods_str
                
            cr.execute(query)
            move_ids = filter(None, map(lambda x:x[0], cr.fetchall()))
            self.write(cr, uid, [wiz.id], { 
                    'move_ids': [(6, 0, move_ids)],
                    'state': 'ready'
                })
        return True

    def action_revalidate_moves(self, cr, uid, ids, context=None):
        """
        Calls the validate method of the account moves for each move in the
        move_ids many2many.
        """
        for wiz in self.browse(cr, uid, ids, context):
            for move in wiz.move_ids:
                # We validate the moves one by one to prevent problems
                self.pool.get('account.move').validate(cr, uid, [move.id], context)
            self.write(cr, uid, [wiz.id], { 'state': 'done' })
        return True

pxgo_revalidate_moves_wizard()


