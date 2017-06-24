# -*- coding: utf-8 -*-
# Copyright 2016 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    equipment_scrap_template_id = fields.Many2one(
        'mail.template',
        related='company_id.equipment_scrap_template_id',
        string='Equipment Scrap Email Template *'
    )
