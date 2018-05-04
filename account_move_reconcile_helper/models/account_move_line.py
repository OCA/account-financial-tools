# -*- coding: utf-8 -*-
##############################################################################
#
#     This file is part of account_move_reconcile_helper,
#     an Odoo module.
#
#     Copyright (c) 2015 ACSONE SA/NV (<http://acsone.eu>)
#
#     account_move_reconcile_helper is free software:
#     you can redistribute it and/or modify it under the terms of the GNU
#     Affero General Public License as published by the Free Software
#     Foundation,either version 3 of the License, or (at your option) any
#     later version.
#
#     account_move_reconcile_helper is distributed
#     in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
#     even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#     PURPOSE.  See the GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public License
#     along with account_move_reconcile_helper.
#     If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields
from openerp.osv import fields as old_fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

# Currenly, isn't possible to use new api to override reconcile_ref because
# addons/account/wizard/account_fiscalyear_close.py uses _store_set_values on
# reconcile_ref

#     @api.one
#     @api.depends('reconcile_id', 'reconcile_partial_id')
#     def _get_reconcile_ref(self):
#         if self.reconcile_id.id:
#             self.reconcile_ref = str(self.reconcile_id.name)
#         elif self.reconcile_partial_id.id:
#             self.reconcile_ref = "P/" + str(self.reconcile_partial_id.name)

    def _get_reconcile(self, cr, uid, ids, name, unknow_none, context=None):
        res = dict.fromkeys(ids, False)
        for line in self.browse(cr, uid, ids, context=context):
            if line.reconcile_id:
                res[line.id] = str(line.reconcile_id.name)
            elif line.reconcile_partial_id:
                res[line.id] = "P/" + str(line.reconcile_partial_id.name)
        return res

    def _get_move_from_reconcile(self, cr, uid, ids, context=None):
        move = {}
        for r in self.pool.get('account.move.reconcile')\
                .browse(cr, uid, ids, context=context):
            for line in r.line_partial_ids:
                move[line.move_id.id] = True
            for line in r.line_id:
                move[line.move_id.id] = True
        move_line_ids = []
        if move:
            move_line_ids = self.pool.get('account.move.line')\
                .search(cr, uid, [('move_id', 'in', move.keys())],
                        context=context)
        return move_line_ids

    _columns = {
        'reconcile_ref': old_fields.function(
            _get_reconcile, type='char', string='Reconcile Ref',
            oldname='reconcile',
            store={'account.move.line': (lambda self, cr, uid, ids, c={}: ids,
                                         ['reconcile_id',
                                          'reconcile_partial_id'], 50),
                   'account.move.reconcile': (_get_move_from_reconcile, None,
                                              50)}),
    }

    credit_debit_balance = fields.Float(compute='compute_debit_credit_balance',
                                        string='Balance')
#     reconcile_ref = fields.Char(compute='_get_reconcile_ref', store=True)

    @api.one
    def compute_debit_credit_balance(self):
        self.credit_debit_balance = self.debit - self.credit
