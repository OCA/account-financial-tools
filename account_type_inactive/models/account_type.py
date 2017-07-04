# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AccountAccountType(models.Model):

    _inherit = 'account.account.type'

    active = fields.Boolean('Active', default=True)

    @api.constrains('active')
    def _check_account_moves(self):
        if not self.active:
            accounts = self.env['account.account'].search([
                ('user_type_id', '=', self.id)])
            if accounts:
                raise ValidationError(_('You cannot inactive this account type'
                                        ' as this type is used on %d '
                                        'accounts.' % len(accounts)))
