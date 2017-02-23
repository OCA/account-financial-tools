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
        res_ids = self.env['account_followup.followup'].search([])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Follow-ups'),
            'res_model': 'account_followup.followup',
            'res_id': res_ids and res_ids[0] or False,
            'view_mode': 'form,tree',
        }
