# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
#    Copyright (c) 2014-2015 Noviat nv/sa (www.noviat.com).
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

from openerp.osv import fields, orm
import logging
_logger = logging.getLogger(__name__)


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def action_number(self, cr, uid, ids, context=None):
        super(account_invoice, self).action_number(cr, uid, ids, context)
        asset_obj = self.pool['account.asset.asset']
        asset_line_obj = self.pool['account.asset.depreciation.line']
        for inv in self.browse(cr, uid, ids):
            move = inv.move_id
            assets = [aml.asset_id for aml in
                      filter(lambda x: x.asset_id, move.line_id)]
            ctx = {'create_asset_from_move_line': True}
            for asset in assets:
                asset_obj.write(
                    cr, uid, [asset.id],
                    {'code': inv.internal_number}, context=ctx)
                asset_line_name = asset_obj._get_depreciation_entry_name(
                    cr, uid, asset, 0)
                asset_line_obj.write(
                    cr, uid, [asset.depreciation_line_ids[0].id],
                    {'name': asset_line_name},
                    context={'allow_asset_line_update': True})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        assets = []
        for inv in self.browse(cr, uid, ids):
            move = inv.move_id
            assets = move and \
                [aml.asset_id for aml in
                 filter(lambda x: x.asset_id, move.line_id)]
        super(account_invoice, self).action_cancel(
            cr, uid, ids, context=context)
        if assets:
            asset_obj = self.pool.get('account.asset.asset')
            asset_obj.unlink(cr, uid, [x.id for x in assets])
        return True

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(account_invoice, self).line_get_convert(
            cr, uid, x, part, date, context=context)
        if x.get('asset_category_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['asset_category_id'] = x['asset_category_id']
        return res

    def inv_line_characteristic_hashcode(self, invoice_line):
        res = super(account_invoice, self).inv_line_characteristic_hashcode(
            invoice_line)
        res += '-%s' % invoice_line.get('asset_category_id', 'False')
        return res


class account_invoice_line(orm.Model):
    _inherit = 'account.invoice.line'

    _columns = {
        'asset_category_id': fields.many2one(
            'account.asset.category', 'Asset Category'),
        'asset_id': fields.many2one(
            'account.asset.asset', 'Asset',
            domain=[('type', '=', 'normal'),
                    ('state', 'in', ['open', 'close'])],
            help="Complete this field when selling an asset "
                 "in order to facilitate the creation of the "
                 "asset removal accounting entries via the "
                 "asset 'Removal' button"),
    }

    def onchange_account_id(self, cr, uid, ids, product_id,
                            partner_id, inv_type, fposition_id, account_id):
        res = super(account_invoice_line, self).onchange_account_id(
            cr, uid, ids, product_id,
            partner_id, inv_type, fposition_id, account_id)
        if account_id:
            asset_category = self.pool['account.account'].browse(
                cr, uid, account_id).asset_category_id
            if asset_category:
                vals = {'asset_category_id': asset_category.id}
                if 'value' not in res:
                    res['value'] = vals
                else:
                    res['value'].update(vals)
        return res

    def move_line_get_item(self, cr, uid, line, context=None):
        res = super(account_invoice_line, self).move_line_get_item(
            cr, uid, line, context)
        if line.asset_category_id:
            res['asset_category_id'] = line.asset_category_id.id
        return res
