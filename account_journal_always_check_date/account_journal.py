# -*- coding: utf-8 -*-
# Copyright 2013-2014 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def init(self, cr):
        '''Activate 'Check Date in Period' on all existing journals'''
        cr.execute(
            "UPDATE AccountJournal SET allow_date=true "
            "WHERE allow_date <> true")
        return True

    allow_date = fields.Boolean(default=True)

    @api.multi
    @api.constrains('allow_date')
    def _allow_date_always_active(self):
        for rec in self:
            if not rec.allow_date:
                raise ValidationError(
                    _("The option 'Check Date in Period' must be active "
                        "on journal '%s'.") % self.name)
