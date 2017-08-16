# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountAssetCategory(models.Model):
    _inherit = "account.asset.category"

    def _default_loss_account_id(self):
        exp_type = self.env.ref('account.data_account_type_expense')
        first_expense = self.env['account.account'].search([
            ('type', '=', 'other'),
            ('user_type', '=', exp_type.id),
        ], limit=1)
        return first_expense

    loss_account_id = fields.Many2one(
        comodel_name="account.account", string="Loss Account", required=True,
        domain=[('type', '=', 'other')],
        default=lambda self: self._default_loss_account_id())
