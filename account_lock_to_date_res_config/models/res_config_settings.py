# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    period_lock_to_date = fields.Date(
        string="Lock To Date for Non-Advisers",
        related='company_id.period_lock_to_date')
    fiscalyear_lock_to_date = fields.Date(
        string="Lock To Date  for All Users",
        related='company_id.fiscalyear_lock_to_date')
