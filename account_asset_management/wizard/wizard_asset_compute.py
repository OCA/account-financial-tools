# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, fields, models, _


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _name = "asset.depreciation.confirmation.wizard"
    _description = "asset.depreciation.confirmation.wizard"

    date_end = fields.Date(
        'Date',
        required=True,
        default=fields.Date.today,
        help="All depreciation lines prior to this date will be automatically"
             " posted")

    @api.multi
    def asset_compute(self):
        self.ensure_one()
        ass_obj = self.env['account.asset']
        assets = ass_obj.search(
            [('state', '=', 'open'), ('type', '=', 'normal')])
        created_move_ids = assets._compute_entries(self.date_end,
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
