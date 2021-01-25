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
        if self.asset_profile_id:
            line_to_create_sum = 0.0
            line_to_create = self.quantity_done
            for line in self.move_line_ids:
                while line_to_create > 1:
                    line_to_create -= 1
                    line_to_create_sum += 1
                    qty = 1.0
                    super(StockMove, self.with_context(dict(self._context, forced_quantity=qty)))._account_entry_move()
            if line_to_create - line_to_create_sum > 0:
                qty = line_to_create - line_to_create_sum
                super(StockMove, self.with_context(dict(self._context, forced_quantity=qty)))._account_entry_move()
        elif self.move_line_ids.mapped('asset_id'):
            line_to_create_sum = 0.0
            line_to_create = self.quantity_done
            for line in self.move_line_ids.filtered(lambda r: r.asset_id):
                line_to_create_sum += 1
                super(StockMove, self.with_context(dict(self._context, forced_quantity=line.qty_done, force_asset=line.asset_id)))._account_entry_move()
            if line_to_create - line_to_create_sum > 0:
                qty = line_to_create - line_to_create_sum
                super(StockMove, self.with_context(dict(self._context, forced_quantity=qty)))._account_entry_move()
        else:
            super(StockMove, self)._account_entry_move()

    @api.multi
    def _get_accounting_data_for_valuation(self):
        journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
        if self._context.get('force_asset'):
            asset = self._context.get('force_asset', self.asset_id)
            if asset:
                journal_id = asset.profile_id.journal_id.id
        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id):
        res = super(StockMove, self)._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id)
        if self.asset_profile_id and self._is_in():
            # _logger.info("ASSET Dt-%s/Ct-%s" % (res[0][2], res[1][2]))
            res[0][2]['asset_profile_id'] = self.asset_profile_id.id
            res[0][2]['tax_profile_id'] = self.tax_profile_id and self.tax_profile_id.id or False
            if len(self.move_line_ids.ids) == 1:
                res[0][2]['move_line_id'] = self.move_line_ids[0].id
                for move_line in self.move_line_ids.filtered(lambda r: r.lot_id):
                    res[0][2]['lot_id'] = move_line.lot_id.id
                    break

        elif self.asset_id or self._context.get('force_asset'):
            asset = self._context.get('force_asset', self.asset_id)
            if asset.state == 'open':
                date = self.accounting_date or self.date
                residual_value = asset._prepare_early_removal(date)
                residual_value = residual_value.get(asset, self.asset_id.value_residual)
                debit_line_vals = res[0][2].copy()
                credit_line_vals = res[1][2]
                res[0][2]['debit'] = credit_line_vals['credit'] - residual_value
                if res[2][2]['product_id']:
                    res[2][2]['asset_id'] = asset
                debit_line_vals['debit'] = residual_value
                debit_line_vals['account_id'] = asset.profile_id.account_depreciation_id.id
                del debit_line_vals['product_id']
                del debit_line_vals['quantity']
                del debit_line_vals['product_uom_id']
                res.append((0, 0, debit_line_vals))
        return res


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
