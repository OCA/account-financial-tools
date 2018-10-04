# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2014-2015 Noviat nv/sa (www.noviat.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models
import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        result = super(AccountInvoice, self).action_number()
        for inv in self:
            move = inv.move_id
            assets = [aml.asset_id for aml in
                      filter(lambda x: x.asset_id, move.line_id)]
            assets = assets.with_context(create_asset_from_move_line=True)
            for asset in assets:
                asset.write({'code': inv.internal_number})
                asset_line_name = asset._get_depreciation_entry_name(0)
                asset.depreciation_line_ids[0].id.with_context(
                    allow_asset_line_update=True).write({
                        'name': asset_line_name})
        return result

    @api.multi
    def action_cancel(self):
        assets = []
        for inv in self:
            move = inv.move_id
            assets = move and \
                [aml.asset_id for aml in
                 filter(lambda x: x.asset_id, move.line_id)]
        result = super(AccountInvoice, self).action_cancel()
        if assets:
            assets.unlink()
        return result

    def line_get_convert(self, x, part, date):
        res = super(AccountInvoice, self).line_get_convert(
            x, part, date)
        if x.get('asset_category_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['asset_category_id'] = x['asset_category_id']
        return res

    def inv_line_characteristic_hashcode(self, invoice_line):
        res = super(AccountInvoice, self).inv_line_characteristic_hashcode(
            invoice_line)
        res += '-%s' % invoice_line.get('asset_category_id', 'False')
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_category_id = fields.Many2one(
        'account.asset.category',
        'Asset Category',
    )
    asset_id = fields.Many2one(
        'account.asset.asset',
        'Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button",
    )

    @api.onchange('account_id')
    def onchange_account_id(self):
        self.asset_category = self.account_id.asset_category_id

    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        if line.asset_category_id:
            res['asset_category_id'] = line.asset_category_id.id
        return res
