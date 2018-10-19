# Copyright 2009-2018 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class AccountAssetProfile(models.Model):

    _name = 'account.asset.profile'
    _inherit = [
        'account.asset.profile', 'account.asset.method.number.end.mixin'
    ]

    @api.model
    def _selection_method_time(self):
        res = super(AccountAssetProfile, self)._selection_method_time()
        res += [
            ('number', _('Number of Depreciations')),
            ('end', _('Ending Date'))]
        return res
