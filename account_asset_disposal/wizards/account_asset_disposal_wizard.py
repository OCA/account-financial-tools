# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountAssetDisposalWizard(models.TransientModel):
    _name = 'account.asset.disposal.wizard'

    def _default_disposal_date(self):
        return fields.Date.context_today(self)

    def _default_loss_account_id(self):
        asset = self.env['account.asset.asset'].browse(
            self.env.context.get('active_id', False)
        )
        return asset.category_id.account_loss_id.id

    disposal_date = fields.Date(
        string="Disposal date", required=True,
        default=lambda self: self._default_disposal_date(),
    )
    loss_account_id = fields.Many2one(
        comodel_name='account.account', string="Loss Account", required=True,
        default=lambda self: self._default_loss_account_id(),
    )

    @api.multi
    def action_dispose(self):
        self.ensure_one()
        assets = self.env['account.asset.asset'].browse(
            self.env.context.get('active_ids', False)
        )
        return assets.dispose(self.disposal_date, self.loss_account_id)
