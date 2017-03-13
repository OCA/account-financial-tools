# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class account_journal(models.Model):
    _inherit = ['account.journal']

    check_chronology = fields.Boolean(string='Check Chronology', default=False)

    @api.one
    @api.onchange('type')
    def on_change_type(self):
        if self.type not in ['sale', 'purchase', 'sale_refund',
                                     'purchase_refund']:
            self.check_chronology = False
        return True
