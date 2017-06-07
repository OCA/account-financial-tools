# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, _


class AccountConfigSettings(models.TransientModel):
    _name = 'account.config.settings'
    _inherit = 'account.config.settings'

    @api.multi
    def open_followup_level_form(self):
        res = self.env['account_followup.followup'].search([
            ('company_id', '=', self.env.user.company_id.id)
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Follow-ups'),
            'res_model': 'account_followup.followup',
            'res_id': res and res.id or False,
            'view_mode': 'form,tree',
        }
