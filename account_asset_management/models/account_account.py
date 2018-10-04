# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2016 Noviat nv/sa (www.noviat.com).
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

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAccount(models.Model):
    _inherit = 'account.account'

    asset_profile_id = fields.Many2one(
        'account.asset.profile',
        name='Asset Profile',
        help="Default Asset Profile when creating invoice lines "
             "with this account.")

    @api.multi
    @api.constrains('asset_profile_id')
    def _check_asset_profile(self):
        for account in self:
            if account.asset_profile_id and \
                    account.asset_profile_id.account_asset_id != account:
                raise ValidationError(_(
                    "The Asset Account defined in the Asset Profile "
                    "must be equal to the account."))
