# -*- coding: utf-8 -*-
from openerp import fields, models, api, _
from openerp.exceptions import Warning


class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'
