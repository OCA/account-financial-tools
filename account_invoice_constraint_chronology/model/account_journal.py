# -*- coding: utf-8 -*-
# © 2014-2016 Acsone SA/NV (http://www.acsone.eu)
# @author: Adrien Peiffer
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    check_chronology = fields.Boolean(string='Check Chronology', default=False)

    @api.one
    @api.constrains('type', 'check_chronology')
    def check_chronology_constrains(self):
        if (
                self.check_chronology and
                self.type not in
                ['sale', 'purchase', 'sale_refund', 'purchase_refund']):
            raise ValidationError(_(
                "Configuration error on journal '%s': the option "
                "'Check Chronology' can only be activated on "
                "journals that can be selected on invoices (i.e. "
                "Sale, Sale Refund, Purchase, Purchase Refund "
                "journals)") % self.name)
