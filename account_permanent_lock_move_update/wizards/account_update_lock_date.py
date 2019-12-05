# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountUpdateLockDate(models.TransientModel):
    _inherit = 'account.update.lock_date'

    tmp_permanent_lock_date = fields.Date(string="Permanent Lock Date")

    @api.model
    def default_get(self, field_list):
        res = super(AccountUpdateLockDate, self).default_get(field_list)
        company = self.env.user.company_id
        res['tmp_permanent_lock_date'] = company.permanent_lock_date
        return res

    def execute(self):
        res = super(AccountUpdateLockDate, self).execute()
        if self.tmp_permanent_lock_date != self.company_id.permanent_lock_date:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'permanent.lock.date.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_company_id': self.company_id.id,
                    'default_lock_date': self.tmp_permanent_lock_date,
                    }
                }
        return res
