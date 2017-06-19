# -*- coding: utf-8 -*-
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_number(self):
        super(AccountInvoice, self).action_number()
        for inv in self:
            move = inv.move_id
            assets = [aml.asset_id for aml in
                      filter(lambda x: x.asset_id, move.line_id)]
            for asset in assets:
                asset.code = inv.internal_number
                asset_line_name = asset._get_depreciation_entry_name(0)
                asset.depreciation_line_ids[0].with_context(
                    {'allow_asset_line_update': True}
                ).name = asset_line_name
        return True

    @api.multi
    def action_cancel(self):
        assets = self.env['account.asset']
        for inv in self:
            move = inv.move_id
            assets = move.line_id.mapped('asset_id')
        super(AccountInvoice, self).action_cancel()
        if assets:
            assets.unlink()
        return True

    @api.model
    def line_get_convert(self, line, part, date):
        res = super(AccountInvoice, self).line_get_convert(line, part, date)
        if line.get('asset_profile_id'):
            # skip empty debit/credit
            if res.get('debit') or res.get('credit'):
                res['asset_profile_id'] = line['asset_profile_id']
        return res

    @api.model
    def inv_line_characteristic_hashcode(self, invoice_line):
        res = super(AccountInvoice, self).inv_line_characteristic_hashcode(
            invoice_line)
        res += '-%s' % invoice_line.get('asset_profile_id', 'False')
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    asset_profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile')
    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")

    @api.multi
    def onchange_account_id(self, product_id, partner_id, inv_type,
                            fposition_id, account_id):
        res = super(AccountInvoiceLine, self).onchange_account_id(
            product_id, partner_id, inv_type, fposition_id, account_id)
        if account_id:
            account = self.env['account.account'].browse(account_id)
            asset_profile = account.asset_profile_id
            if asset_profile:
                vals = {'asset_profile_id': asset_profile.id}
                if 'value' not in res:
                    res['value'] = vals
                else:
                    res['value'].update(vals)
        return res

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        if line.asset_profile_id:
            res['asset_profile_id'] = line.asset_profile_id.id
        return res
