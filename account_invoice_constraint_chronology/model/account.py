# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountJournal(models.Model):
    _inherit = ['account.journal']

    check_chronology = fields.Boolean(default=False)

    @api.onchange('type')
    def _onchange_type(self):
        if self.type not in ['sale', 'purchase']:
            self.check_chronology = False
