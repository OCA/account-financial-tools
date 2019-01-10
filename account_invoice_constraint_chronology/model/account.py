# -*- coding: utf-8 -*-


from openerp import models, fields, api


class AccountJournal(models.Model):
    _inherit = ['account.journal']

    check_chronology = fields.Boolean(default=False)

    @api.onchange('type')
    def _onchange_type(self):
        if self.type not in ['sale', 'purchase']:
            self.check_chronology = False
