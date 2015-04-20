# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 ACSONE SA/NV (http://acsone.eu).
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

from openerp.osv import orm, fields


class Config(orm.TransientModel):
    _inherit = 'account.config.settings'

    _columns = {
        'module_account_asset_management': fields.boolean(
            'Assets management (OCA)',
            help="""This allows you to manage the assets owned by a company
                    or a person. It keeps track of the depreciation occurred
                    on those assets, and creates account move for those
                    depreciation lines.
                    This installs the module account_asset_management."""),
    }
