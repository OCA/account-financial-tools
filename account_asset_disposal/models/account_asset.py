# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# Copyright 2017 Luis M. Ontalba - <luis.martinez@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models


class AccountAssetCategory(models.Model):
    _inherit = "account.asset.category"

    def _default_loss_account_id(self):
        exp_type = self.env.ref('account.data_account_type_expenses')
        first_expense = self.env['account.account'].search([
            ('internal_type', '=', 'other'),
            ('user_type_id', '=', exp_type.id),
        ], limit=1)
        return first_expense

    loss_account_id = fields.Many2one(
        comodel_name="account.account", string="Loss Account", required=True,
        domain=[('internal_type', '=', 'other')],
        default=lambda self: self._default_loss_account_id())


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    state = fields.Selection(
        selection_add=[('disposed', 'Disposed')],
    )
    disposal_date = fields.Date(string="Disposal date")
    disposal_move_id = fields.Many2one(
        comodel_name='account.move', string="Disposal move")

    def get_disposal_date(self):
        return fields.Date.context_today(self)

    @api.multi
    def set_to_close(self):
        value_residual_prev = self.value_residual
        res = super(AccountAssetAsset, self).set_to_close()
        if res:
            date = self.get_disposal_date()
            loss_account = self.category_id.loss_account_id
            self.value_residual = value_residual_prev
            move = self.disposal_move_create(date, loss_account)
            res['res_id'] = move.id
            self.disposal_move_id = res['res_id']
            self.disposal_move_id.post()
        self.write({
            'state': 'disposed',
            'disposal_date': self.get_disposal_date(),
        })
        return res

    @api.multi
    def action_disposal_undo(self):
        for asset in self.with_context(asset_disposal_undo=True):
            if asset.disposal_move_id:
                asset.disposal_move_id.button_cancel()
                asset.disposal_move_id.unlink()
            last_line = self.depreciation_line_ids[-1]
            last_line.move_id = False
            last_line.unlink()
            asset.state = 'open'
            asset.method_end = asset.category_id.method_end
            asset.method_number = asset.category_id.method_number
            asset.compute_depreciation_board()
        return self.write({
            'disposal_date': False,
            'disposal_move_id': False,
        })

    def _disposal_line_asset_prepare(self, date, journal):
        return {
            'name': _('Asset disposal'),
            'journal_id': journal.id,
            'account_id': self.category_id.account_asset_id.id,
            'date': date,
            'debit': 0.0,
            'credit': self.value,
        }

    def _disposal_line_depreciation_prepare(self, date, journal,
                                            depreciation_value):
        return {
            'name': _('Asset depreciation'),
            'journal_id': journal.id,
            'account_id': self.category_id.account_depreciation_id.id,
            'date': date,
            'debit': depreciation_value,
            'credit': 0.0,
        }

    def _disposal_line_loss_prepare(self, date, journal, loss_account,
                                    loss_value):
        return {
            'name': _('Asset loss'),
            'journal_id': journal.id,
            'account_id': loss_account.id,
            'analytic_account_id': self.category_id.account_analytic_id.id,
            'date': date,
            'debit': loss_value,
            'credit': 0.0,
        }

    def _disposal_move_prepare(self, date, loss_account):
        journal = self.category_id.journal_id
        loss_value = self.salvage_value + self.value_residual
        depreciation_value = self.value - loss_value
        line_asset = self._disposal_line_asset_prepare(date, journal)
        line_depreciation = self._disposal_line_depreciation_prepare(
            date, journal, depreciation_value)
        lines = [
            (0, False, line_asset),
            (0, False, line_depreciation),
        ]
        if loss_value:
            line_loss = self._disposal_line_loss_prepare(
                date, journal, loss_account, loss_value)
            lines.append((0, False, line_loss))
        return {
            'journal_id': journal.id,
            'ref': self.name,
            'date': date,
            'line_ids': lines,
        }

    def disposal_move_create(self, date, loss_account):
        vals = self._disposal_move_prepare(date, loss_account)
        move = self.env['account.move'].create(vals)
        return move


class AccountAssetDepreciationLine(models.Model):
    _inherit = 'account.asset.depreciation.line'

    @api.multi
    def post_lines_and_close_asset(self):
        disposed_lines = self.filtered(lambda r: r.asset_id.state ==
                                       'disposed')
        super(AccountAssetDepreciationLine, self).post_lines_and_close_asset()
        disposed_lines.mapped('asset_id').write({'state': 'disposed'})
