# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountAssetCategory(models.Model):
    _inherit = "account.asset.category"

    account_loss_id = fields.Many2one(
        comodel_name="account.account", string="Loss Account",
        oldname='loss_account_id',
    )
