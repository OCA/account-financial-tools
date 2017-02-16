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

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        super(AccountInvoice, self).action_number()
        for inv in self:
            move = inv.move_id
            assets = [aml.asset_id for aml in
                      filter(lambda x: x.asset_id, move.line_ids)]
            for asset in assets:
                asset.code = inv.internal_number
                asset_line_name = asset._get_depreciation_entry_name()
                asset.depreciation_line_ids[0].with_context(
                    {'allow_asset_line_update': True}
                    ).name = asset_line_name
        return True

    @api.multi
    def action_cancel(self):
        for inv in self:
            move = inv.move_id
            assets = move.line_ids.mapped('asset_id')
        super(AccountInvoice, self).action_cancel()
        if assets:
            assets.unlink()
        return True

    @api.model
    def line_get_convert(self, x, part):
        res = super(AccountInvoice, self).line_get_convert(
            x, part)
        if x.get('asset_profile_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['asset_profile_id'] = x['asset_profile_id']
        return res

    @api.model
    def inv_line_characteristic_hashcode(self, invoice_line):
        res = super(AccountInvoice, self).inv_line_characteristic_hashcode(
            invoice_line)
        res += '-%s' % invoice_line.get('asset_profile_id', 'False')
        return res

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()
        invoice_line_obj = self.env['account.invoice.line']
        for vals in res:
            invline = invoice_line_obj.browse(vals['invl_id'])
            if invline.asset_profile_id:
                vals['asset_profile_id'] = invline.asset_profile_id.id
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_profile_id = fields.Many2one(
        'account.asset.profile',
        string='Asset Profile')
    asset_id = fields.Many2one(
        'account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")

    @api.onchange('account_id')
    def _onchange_account_id(self):
        self.asset_profile_id = self.account_id.asset_profile_id.id
