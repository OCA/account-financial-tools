# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountUpdateLockDate(models.TransientModel):

    _inherit = 'account.update.lock_date'

    permanent_lock_date = fields.Date(
        string="Permanent Lock Date", readonly=True)

    @api.model
    def default_get(self, field_list):
        res = super(AccountUpdateLockDate, self).default_get(field_list)
        company = self.env.user.company_id
        res['permanent_lock_date'] = company.permanent_lock_date
        return res

    @api.multi
    def change_permanent_lock_date(self):
        self.ensure_one()
        company = self.company_id
        wizard = self.env['permanent.lock.date.wizard'].create({
            'company_id': company.id,
            'lock_date': company.permanent_lock_date,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'permanent.lock.date.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }
