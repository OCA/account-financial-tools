# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools import float_compare


class AccountAssetForceRemove(models.TransientModel):
    _name = "account.asset.force.remove"
    _description = "Force remove account asset files"

    asset_ids = fields.Many2many('account.asset', string='Assets for update', required=True)
    force_delete = fields.Boolean('Force delete')
    force_unlink = fields.Boolean('Force unlink')
    account_line_ids = fields.One2many('account.asset.force.remove.line', 'force_id', 'Account replacements lines')
    account_ids = fields.Many2many('account.account', 'True accounts', compute='_compute_account_ids')
    company_id = fields.Many2one('res.company', 'Company')

    @api.multi
    @api.depends('asset_ids')
    def _compute_account_ids(self):
        for record in self:
            for asset_id in record.asset_ids:
                am_ids = self.env['account.move.line'].search([('asset_id', '=', asset_id.id)], order='date ASC')
                am_ids |= asset_id.depreciation_line_ids.mapped('move_id').mapped('line_ids')
                record.account_ids = am_ids.mapped('account_id')

    @api.model
    def default_get(self, fields_list):
        res = super(AccountAssetForceRemove, self).default_get(fields_list)
        if self._context.get('active_model') == 'account.asset':
            asset_ids = self.env['account.asset'].browse(self._context['active_ids'])
            am_ids = False
            for asset_id in asset_ids:
                am_ids = self.env['account.move.line'].search([('asset_id', '=', asset_id.id)], order='date ASC')
                am_ids |= asset_id.depreciation_line_ids.mapped('move_id').mapped('line_ids')
            res.update({
                'asset_ids': [(6, False, asset_ids.ids)],
                'account_ids': am_ids and [(6, False, am_ids)] or False,
                'company_id': self.env.user.company_id.id,
            })
        return res

    @api.multi
    def add_force(self):
        for record in self:
            for asset_id in record.asset_ids:
                if asset_id:
                    account_move_ids = []
                    am_ids = self.env['account.move.line'].search([('asset_id', '=', asset_id.id)], order='date ASC')
                    am_ids |= asset_id.depreciation_line_ids.mapped('move_id').mapped('line_ids')
                    if len(record.account_line_ids.ids) > 0:
                        account_move_ids = am_ids.mapped('move_id')
                    for line in account_move_ids:
                        line.button_cancel()
                    for line in am_ids:
                        values = {}
                        if record.force_unlink or record.force_delete:
                            values.update({
                                'asset_id': False
                            })
                        for account_id in record.account_line_ids.\
                                filtered(lambda r: r.original_account_id == line.account_id):
                            values.update({
                                'account_id': account_id.replace_account_id.id
                            })
                        line.with_context(dict(self._context, allow_asset_removal=True, allow_asset=True)).write(values)
                    for line in account_move_ids:
                        line.post()
                    if record.force_unlink or record.force_delete:
                        for depreciation_line_id in asset_id.depreciation_line_ids:
                            depreciation_line_id.with_context(dict(self._context, unlink_from_asset=True)).write({
                               'move_id': False
                            })

                    asset_id.set_to_draft()
                    if self.force_delete:
                        asset_id.unlink()


class AccountAssetForceRemoveLine(models.TransientModel):
    _name = "account.asset.force.remove.line"
    _description = "Force remove account asset files mapper for accounts"

    force_id = fields.Many2one('account.asset.force.remove', 'Wizard for account asset update',
                               index=True, required=True, ondelete='cascade')
    original_account_id = fields.Many2one('account.account', 'Original account')
    replace_account_id = fields.Many2one('account.account', 'Replacements account')
