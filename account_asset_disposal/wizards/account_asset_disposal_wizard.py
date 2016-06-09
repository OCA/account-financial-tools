# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountAssetDisposalWizard(models.TransientModel):
    _name = 'account.asset.disposal.wizard'

    def _default_disposal_date(self):
        return fields.Date.context_today(self)

    def _default_loss_account_id(self):
        return self.env['account.asset.category']._default_loss_account_id()

    disposal_date = fields.Date(
        string="Disposal date", require=True,
        default=lambda self: self._default_disposal_date())
    loss_account_id = fields.Many2one(
        comodel_name='account.account', string="Loss account", require=True,
        domain=[('type', '=', 'other')],
        default=lambda self: self._default_loss_account_id())

    def _disposal_date_set(self, assets):
        assets.write({'disposal_date': self.disposal_date})

    @api.multi
    def action_disposal(self):
        self.ensure_one()
        assets = self.env['account.asset.asset'].browse(
            self.env.context.get('active_ids', False))
        for asset in assets:
            asset.disposal_move_create(
                self.disposal_date, self.loss_account_id)
        self._disposal_date_set(assets)
        return assets.set_to_close()
