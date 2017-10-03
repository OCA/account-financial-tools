# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class PermanentLockDateWizard(models.TransientModel):

    _inherit = 'permanent.lock.date.wizard'

    @api.multi
    def confirm_date(self):
        has_adviser_group = self.env.user.has_group(
            'account.group_account_manager')
        if has_adviser_group:
            self = self.sudo()
        return super(PermanentLockDateWizard, self).confirm_date()
