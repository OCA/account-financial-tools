# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models
from openerp.tools.safe_eval import safe_eval


class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def _get_amlse_act_id(self):
        module = 'account_move_line_search_extension'
        xml_id = 'action_account_move_line_search_extension'
        self.env.cr.execute(
            "SELECT res_id from ir_model_data "
            "WHERE model = 'ir.actions.act_window' "
            "AND module = %s AND name = %s ",
            (module, xml_id))
        res = self.env.cr.fetchone()
        return res and res[0]

    def __init__(self, pool, cr):
        self._amlse_act_id = self._get_amlse_act_id(cr)
        super(IrActionsActWindow, self).__init__(pool, cr)

    def _amlse_add_groups(self):
        groups = {}
        if self.env['res.users'].has_group(
                'analytic.group_analytic_accounting'):
            groups['group_analytic'] = 1
        return groups

    @api.multi
    def read(self, fields=None, load='_classic_read'):
        res = super(IrActionsActWindow, self).read(fields=fields, load=load)
        if not self._amlse_act_id:
            self._amlse_act_id = self._get_amlse_act_id()
        if self.ids == [self._amlse_act_id]:
            amlse_act = res[0]
            if amlse_act.get('context'):
                act_ctx = safe_eval(amlse_act['context'])
                act_ctx.update(self._amlse_add_groups())
                amlse_act['context'] = str(act_ctx)
        return res
