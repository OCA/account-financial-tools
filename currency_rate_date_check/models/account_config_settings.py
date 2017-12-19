# coding: utf-8
# © 2016 Today Akretion
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    currency_rate_max_delta = fields.Integer(
        related='company_id.currency_rate_max_delta')
