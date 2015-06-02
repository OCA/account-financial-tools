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

from openerp.osv import fields, orm
from openerp.tools.translate import _
import logging
_logger = logging.getLogger(__name__)

# List of move's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE = set(['period_id', 'journal_id', 'date'])
# List of move line's fields that can't be modified if move is linked
# with a depreciation line
FIELDS_AFFECTS_ASSET_MOVE_LINE = \
    set(['credit', 'debit', 'account_id', 'journal_id', 'date',
         'asset_category_id', 'asset_id', 'tax_code_id', 'tax_amount'])


class account_move(orm.Model):
    _inherit = 'account.move'

    def unlink(self, cr, uid, ids, context=None, check=True):
        if not context:
            context = {}
        depr_obj = self.pool.get('account.asset.depreciation.line')
        for move_id in ids:
            depr_ids = depr_obj.search(
                cr, uid,
                [('move_id', '=', move_id),
                 ('type', 'in', ['depreciate', 'remove'])])
            if depr_ids and not context.get('unlink_from_asset'):
                raise orm.except_orm(
                    _('Error!'),
                    _("You are not allowed to remove an accounting entry "
                      "linked to an asset."
                      "\nYou should remove such entries from the asset."))
            # trigger store function
            depr_obj.write(cr, uid, depr_ids, {'move_id': False}, context)
        return super(account_move, self).unlink(
            cr, uid, ids, context=context, check=check)

    def write(self, cr, uid, ids, vals, context=None):
        if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE):
            if isinstance(ids, (int, long)):
                ids = [ids]
            depr_obj = self.pool.get('account.asset.depreciation.line')
            for move_id in ids:
                depr_ids = depr_obj.search(
                    cr, uid,
                    [('move_id', '=', move_id), ('type', '=', 'depreciate')])
                if depr_ids:
                    raise orm.except_orm(
                        _('Error!'),
                        _("You cannot change an accounting entry "
                          "linked to an asset depreciation line."))
        return super(account_move, self).write(cr, uid, ids, vals, context)


class account_move_line(orm.Model):
    _inherit = 'account.move.line'

    _columns = {
        'asset_category_id': fields.many2one(
            'account.asset.category', 'Asset Category'),
    }

    def onchange_account_id(self, cr, uid, ids,
                            account_id=False, partner_id=False, context=None):
        res = super(account_move_line, self).onchange_account_id(
            cr, uid, ids, account_id, partner_id, context)
        account_obj = self.pool.get('account.account')
        if account_id:
            account = account_obj.browse(cr, uid, account_id)
            asset_category = account.asset_category_id
            if asset_category:
                res['value'].update({'asset_category_id': asset_category.id})
        return res

    def create(self, cr, uid, vals, context=None, check=True):
        if not context:
            context = {}
        if vals.get('asset_id') and not context.get('allow_asset'):
            raise orm.except_orm(_(
                'Error!'),
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_category_id'):
            asset_obj = self.pool.get('account.asset.asset')
            # create asset
            move = self.pool.get('account.move').browse(
                cr, uid, vals['move_id'])
            asset_value = vals['debit'] or -vals['credit']
            asset_vals = {
                'name': vals['name'],
                'category_id': vals['asset_category_id'],
                'purchase_value': asset_value,
                'partner_id': vals['partner_id'],
                'date_start': move.date,
            }
            if context.get('company_id'):
                asset_vals['company_id'] = context['company_id']
            changed_vals = asset_obj.onchange_category_id(
                cr, uid, [], vals['asset_category_id'], context=context)
            asset_vals.update(changed_vals['value'])
            ctx = dict(context, create_asset_from_move_line=True,
                       move_id=vals['move_id'])
            asset_id = asset_obj.create(cr, uid, asset_vals, context=ctx)
            vals['asset_id'] = asset_id

        return super(account_move_line, self).create(
            cr, uid, vals, context, check)

    def write(self, cr, uid, ids, vals,
              context=None, check=True, update_check=True):
        for move_line in self.browse(cr, uid, ids, context=context):
            if move_line.asset_id.id:
                if set(vals).intersection(FIELDS_AFFECTS_ASSET_MOVE_LINE):
                    raise orm.except_orm(
                        _('Error!'),
                        _("You cannot change an accounting item "
                          "linked to an asset depreciation line."))
        if vals.get('asset_id'):
            raise orm.except_orm(
                _('Error!'),
                _("You are not allowed to link "
                  "an accounting entry to an asset."
                  "\nYou should generate such entries from the asset."))
        if vals.get('asset_category_id'):
            assert len(ids) == 1, \
                'This option should only be used for a single id at a time.'
            asset_obj = self.pool.get('account.asset.asset')
            for aml in self.browse(cr, uid, ids, context):
                if vals['asset_category_id'] == aml.asset_category_id.id:
                    continue
                # create asset
                debit = 'debit' in vals and vals.get('debit', 0.0) or aml.debit
                credit = 'credit' in vals and \
                    vals.get('credit', 0.0) or aml.credit
                asset_value = debit - credit
                partner_id = 'partner' in vals and \
                    vals.get('partner', False) or aml.partner_id.id
                date_start = 'date' in vals and \
                    vals.get('date', False) or aml.date
                asset_vals = {
                    'name': vals.get('name') or aml.name,
                    'category_id': vals['asset_category_id'],
                    'purchase_value': asset_value,
                    'partner_id': partner_id,
                    'date_start': date_start,
                    'company_id': vals.get('company_id') or aml.company_id.id,
                }
                changed_vals = asset_obj.onchange_category_id(
                    cr, uid, [], vals['asset_category_id'], context=context)
                asset_vals.update(changed_vals['value'])
                ctx = dict(context, create_asset_from_move_line=True,
                           move_id=aml.move_id.id)
                asset_id = asset_obj.create(cr, uid, asset_vals, context=ctx)
                vals['asset_id'] = asset_id

        return super(account_move_line, self).write(
            cr, uid, ids, vals, context, check, update_check)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
