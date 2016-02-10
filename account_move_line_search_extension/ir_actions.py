# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models
from openerp.tools.safe_eval import safe_eval


class ir_actions_act_window(models.Model):
    _inherit = 'ir.actions.act_window'

    def _get_amlse_act_id(self, cr):
        module = 'account_move_line_search_extension'
        xml_id = 'action_account_move_line_search_extension'
        cr.execute(
            "SELECT res_id from ir_model_data "
            "WHERE model = 'ir.actions.act_window' "
            "AND module = %s AND name = %s ",
            (module, xml_id))
        res = cr.fetchone()
        return res and res[0]

    def __init__(self, pool, cr):
        self._amlse_act_id = self._get_amlse_act_id(cr)
        super(ir_actions_act_window, self).__init__(pool, cr)

    def _amlse_add_groups(self, cr, uid, context):
        groups = {}
        if self.pool['res.users'].has_group(
                cr, uid, 'analytic.group_analytic_accounting'):
            groups['group_analytic'] = 1
        return groups

    def read(self, cr, uid, ids, fields=None,
             context=None, load='_classic_read'):
        if not context:
            context = {}
        res = super(ir_actions_act_window, self).read(
            cr, uid, ids, fields=fields, context=context, load=load)
        if not self._amlse_act_id:
            self._amlse_act_id = self._get_amlse_act_id(cr)
        if ids == [self._amlse_act_id]:
            amlse_act = res[0]
            if amlse_act.get('context'):
                act_ctx = safe_eval(amlse_act['context'])
                act_ctx.update(self._amlse_add_groups(cr, uid, context))
                amlse_act['context'] = str(act_ctx)
        return res
