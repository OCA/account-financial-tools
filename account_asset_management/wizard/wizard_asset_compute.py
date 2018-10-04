# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _name = "asset.depreciation.confirmation.wizard"
    _description = "asset.depreciation.confirmation.wizard"

    def _get_period(self):
        self = self.with_context(account_period_prefer_normal=True)
        periods = self.env['account.period'].find()
        if periods:
            return periods[0]
        return False

    period_id = fields.Many2one(
        'account.period',
        'Period',
        domain="[('special', '=', False), ('state', '=', 'draft')]",
        required=True,
        help="Choose the period for which you want to automatically "
             "post the depreciation lines of running assets",
        default=_get_period,
    )

    @api.multi
    def asset_compute(self):
        self.ensure_one()
        ass_obj = self.env['account.asset.asset']
        asset_ids = ass_obj.search([
            ('state', '=', 'open'),
            ('type', '=', 'normal')],
        )
        period_id = self.period_id.id
        created_move_ids = asset_ids._compute_entries(
            period_id,
            check_triggers=True)
        domain = "[('id', 'in', [" + \
            ','.join(map(str, created_move_ids)) + "])]"
        return {
            'name': _('Created Asset Moves'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'domain': domain,
            'type': 'ir.actions.act_window',
        }
