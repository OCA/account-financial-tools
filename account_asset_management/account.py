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

import time
from openerp.osv import orm, fields
from openerp import tools
from openerp import SUPERUSER_ID


class account_account(orm.Model):
    _inherit = 'account.account'

    _columns = {
        'asset_category_id': fields.many2one(
            'account.asset.category', 'Asset Category',
            help="Default Asset Category when creating invoice lines "
                 "with this account."),
    }

    def _check_asset_categ(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        for account in self.browse(cr, uid, ids, context=context):
            if account.asset_category_id and \
                    account.asset_category_id.account_asset_id != account:
                return False
        return True

    _constraints = [
        (_check_asset_categ,
         "The Asset Account defined in the Asset Category "
         "must be equal to the account.",
         ['asset_categ_id']),
    ]


class account_fiscalyear(orm.Model):
    _inherit = 'account.fiscalyear'

    def create(self, cr, uid, vals, context=None):
        # To DO :
        # change logic to avoid table recompute overhead
        # when a regular (duration = 1 year) new FY is created
        recompute_obj = self.pool.get('account.asset.recompute.trigger')
        user_obj = self.pool.get('res.users')
        recompute_vals = {
            'reason': 'creation of fiscalyear %s' % vals.get('code'),
            'company_id':
                vals.get('company_id') or
                user_obj.browse(cr, uid, uid, context).company_id.id,
            'date_trigger': time.strftime(
                tools.DEFAULT_SERVER_DATETIME_FORMAT),
            'state': 'open',
        }
        recompute_obj.create(
            cr, SUPERUSER_ID, recompute_vals, context=context)
        return super(account_fiscalyear, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if vals.get('date_start') or vals.get('date_stop'):
            recompute_obj = self.pool.get('account.asset.recompute.trigger')
            fy_datas = self.read(cr, uid, ids, ['code', 'company_id'])
            for fy_data in fy_datas:
                recompute_vals = {
                    'reason':
                        'duration change of fiscalyear %s' % fy_data['code'],
                    'company_id': fy_data['company_id'][0],
                    'date_trigger':
                        time.strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
                    'state': 'open',
                }
                recompute_obj.create(
                    cr, SUPERUSER_ID, recompute_vals, context=context)
        return super(account_fiscalyear, self).write(
            cr, uid, ids, vals, context=context)
