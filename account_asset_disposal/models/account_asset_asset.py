# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, _


class AccountAssetAsset(models.Model):
    _inherit = "account.asset.asset"

    state = fields.Selection(
        selection_add=[('disposed', 'Disposed')],
    )
    disposal_date = fields.Date(string="Disposal date")
    disposal_move_id = fields.Many2one(
        comodel_name='account.move', string="Disposal move")

    def _disposal_line_asset_prepare(self, date, period, journal):
        return {
            'name': _('Asset disposal'),
            'journal_id': journal.id,
            'period_id': period.id,
            'account_id': self.category_id.account_asset_id.id,
            'asset_id': self.id,
            'date': date,
            'debit': 0.0,
            'credit': self.purchase_value,
        }

    def _disposal_line_depreciation_prepare(self, date, period, journal,
                                            depreciation_value):
        return {
            'name': _('Asset depreciation'),
            'journal_id': journal.id,
            'period_id': period.id,
            'account_id': self.category_id.account_depreciation_id.id,
            'asset_id': self.id,
            'date': date,
            'debit': depreciation_value,
            'credit': 0.0,
        }

    def _disposal_line_loss_prepare(self, date, period, journal, loss_account,
                                    loss_value):
        return {
            'name': _('Asset loss'),
            'journal_id': journal.id,
            'period_id': period.id,
            'account_id': loss_account.id,
            'analytic_account_id': self.category_id.account_analytic_id.id,
            'asset_id': self.id,
            'date': date,
            'debit': loss_value,
            'credit': 0.0,
        }

    def _disposal_move_prepare(self, date, loss_account):
        journal = self.category_id.journal_id
        period = self.env['account.period'].find(date)
        loss_value = self.salvage_value + self.value_residual
        depreciation_value = self.purchase_value - loss_value
        line_asset = self._disposal_line_asset_prepare(date, period, journal)
        line_depreciation = self._disposal_line_depreciation_prepare(
            date, period, journal, depreciation_value)
        lines = [
            (0, False, line_asset),
            (0, False, line_depreciation),
        ]
        if loss_value:
            line_loss = self._disposal_line_loss_prepare(
                date, period, journal, loss_account, loss_value)
            lines.append((0, False, line_loss))
        return {
            'journal_id': journal.id,
            'period_id': period.id,
            'ref': self.name,
            'date': date,
            'line_id': lines,
        }

    @api.multi
    def disposal_move_create(self, date, loss_account):
        for asset in self:
            vals = self._disposal_move_prepare(date, loss_account)
            asset.disposal_move_id = self.env['account.move'].create(vals)
            if asset.disposal_move_id:
                asset.disposal_move_id.post()

    @api.multi
    def action_disposal(self):
        wizard_view_id = self.env.ref(
            'account_asset_disposal.account_asset_disposal_wizard_form')
        return {
            'name': 'Disposal asset',
            'res_model': 'account.asset.disposal.wizard',
            'type': 'ir.actions.act_window',
            'view_type': 'tree,form',
            'view_mode': 'form',
            'view_id': wizard_view_id.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def action_disposal_undo(self):
        for asset in self.with_context(asset_disposal_undo=True):
            if asset.disposal_move_id:
                asset.disposal_move_id.button_cancel()
                asset.disposal_move_id.unlink()
            if asset.currency_id.is_zero(asset.value_residual):
                asset.state = 'close'
            else:
                asset.state = 'open'
        return self.write({
            'disposal_date': False,
            'disposal_move_id': False,
        })
