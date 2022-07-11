# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when selling an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")
    asset_profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile')
    tax_profile_id = fields.Many2one(
        comodel_name='account.bg.asset.profile',
        string='Tax Asset Profile')

    # edit_accounts = fields.Boolean(string='Edit accounts')

    # def _is_out(self):
    #     if not self.asset_id:
    #         return super(StockMove, self)._is_out()
    #     return False

    def _get_new_picking_values(self):
        vals = super(StockMove, self)._get_new_picking_values()
        vals['asset_id'] = self.sale_line_id.asset_id.id
        if self.sale_line_id.asset_id:
            vals['asset_id'] = self.sale_line_id.asset_id.id,
        return vals

    def _account_entry_move(self):
        if not self.asset_profile_id and self.move_line_ids.mapped('asset_id').filtered(lambda r: not r.to_sell):
            if self._context.get('force_asset'):
                force_asset = self._context['force_asset']
            else:
                force_asset = self.move_line_ids.mapped('asset_id').filtered(lambda r: not r.to_sell)
            allow_asset_removal = self._is_out()
            allow_asset = self._is_in()
            date = self.date
            if len(force_asset.ids) > 1:
                force_asset = force_asset[0]
            if force_asset.date_start.year == date.year:
                force_asset.to_sell = True
                force_asset = False
                allow_asset_removal = False
            if allow_asset_removal and force_asset.state == 'draft' and force_asset.date_start.year != date.year:
                force_asset.validate()
                force_asset.compute_depreciation_board()
                force_asset.with_context(dict(self._context, bg_asset_line=True)).compute_depreciation_board()
            super(StockMove, self).with_context(dict(self._context,
                                                     force_asset=force_asset,
                                                     allow_asset_removal=allow_asset_removal,
                                                     allow_asset=allow_asset))._account_entry_move()
            if allow_asset_removal:
                force_asset.with_context(dict(self._context, asset_out=True)).validate()
        else:
            super(StockMove, self)._account_entry_move()

    @api.multi
    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if self._context.get('force_asset'):
            asset = self._context.get('force_asset', False)
            if asset and asset.profile_id.journal_stock_move_id:
                journal_id = asset.profile_id.journal_stock_move_id.id
        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        # _logger.info("RES %s" % res)
        if not self.asset_profile_id and self._context.get('force_asset') and self._is_in():
            asset = self._context.get('force_asset')
            res[0][2]['asset_id'] = asset.id
            res[1][2]['asset_id'] = asset.id

        # if self.asset_profile_id and not self.move_line_ids.mapped('asset_id') and self._is_in():
        #     # _logger.info("ASSET Dt-%s/Ct-%s" % (res[0][2], res[1][2]))
        #     res[0][2]['asset_profile_id'] = self.asset_profile_id.id
        #     res[0][2]['tax_profile_id'] = self.tax_profile_id and self.tax_profile_id.id or False
        #     if len(self.move_line_ids.ids) == 1:
        #         res[0][2]['move_line_id'] = self.move_line_ids[0].id
        #         for move_line in self.move_line_ids.filtered(lambda r: r.lot_id):
        #             res[0][2]['lot_id'] = move_line.lot_id.id
        #             break

        if self._context.get('force_asset') and self._is_out():
            asset = self._context.get('force_asset')
            if asset.state == 'open':
                date = self.accounting_date or self.date
                residual_value = asset._prepare_early_removal(date)
                residual_value = residual_value.get(asset, self.asset_id.value_residual)
                debit_line_vals = res[0][2].copy()
                credit_line_vals = res[1][2]
                res[0][2]['debit'] = credit_line_vals['credit'] - residual_value
                res[0][2]['asset_id'] = asset.id
                res[1][2]['asset_id'] = asset.id
                debit_line_vals['debit'] = residual_value
                debit_line_vals['account_id'] = asset.profile_id.account_depreciation_id.id
                debit_line_vals['asset_id'] = asset.id
                del debit_line_vals['product_id']
                del debit_line_vals['quantity']
                del debit_line_vals['product_uom_id']
                res.append((0, 0, debit_line_vals))
        return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id):
        if not self._context.get('allow_asset') and self._is_out() and any([r.asset_id for r in self.move_line_ids]):
            return super(StockMove, self).with_context(dict(self._context, allow_asset=True))._create_account_move_line(credit_account_id, debit_account_id, journal_id)
        return super(StockMove, self)._create_account_move_line(credit_account_id, debit_account_id, journal_id)

    @api.multi
    def _check_for_assets(self):
        check = {}
        for record in self:
            if len(record.mapped('move_line_ids').mapped('asset_id').ids) > 0:
                continue
            # Check in product valuations
            product_tmpl = record.product_id.product_tmpl_id.categ_id
            if product_tmpl.property_stock_valuation_account_id and product_tmpl.property_stock_valuation_account_id.asset_profile_id:
                check[record] = {
                    'asset_profile_id': product_tmpl.property_stock_valuation_account_id.asset_profile_id,
                    'tax_profile_id': product_tmpl.property_stock_valuation_account_id.tax_profile_id,
                }
        return check


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    asset_id = fields.Many2one(
        comodel_name='account.asset',
        string='Asset',
        domain=[('type', '=', 'normal'),
                ('state', 'in', ['open', 'close'])],
        help="Complete this field when use an asset "
             "in order to facilitate the creation of the "
             "asset removal accounting entries via the "
             "asset 'Removal' button")

    @api.onchange('lot_name', 'lot_id')
    def onchange_serial_number(self):
        res = super(StockMoveLine, self).onchange_serial_number()
        if self.product_id and self.lot_id:
            asset = self.env['account.asset'].search([('company_id', '=', self.move_id.company_id.id),
                                                      ('product_id', '=', self.product_id.id),
                                                      ('lot_id', '=', self.lot_id.id)], limit=1)
            if asset:
                self.asset_id = asset
        return res

    @api.model
    def create(self, vals):
        if vals.get('product_id') and vals.get('lot_id') and not vals.get('asset_id'):
            asset = self.env['account.asset'].search([('product_id', '=', vals['product_id']),
                                                      ('lot_id', '=', vals['lot_id'])])
            if asset:
                vals['asset_id'] = asset.id
        return super(StockMoveLine, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('lot_id'):
            for record in self:
                product_id = vals.get('product_id') or record.product_id.id
                asset = self.env['account.asset'].search([('product_id', '=', product_id),
                                                          ('lot_id', '=', vals['lot_id'])])
                if asset and len(asset.ids) == 1 and self.asset_id != asset or not vals.get('asset_id'):
                    vals['asset_id'] = asset.id
        return super(StockMoveLine, self).write(vals)
