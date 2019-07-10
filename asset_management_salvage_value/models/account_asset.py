# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    @api.multi
    def button_edit_salvage(self):
        """ Return Wizard to Edit Salvage Value """
        action = self.env.ref('asset_management_salvage_value.'
                              'action_view_asset_salvage_value')
        vals = action.read()[0]
        return vals
