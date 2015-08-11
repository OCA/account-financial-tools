# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields


class account_journal(models.Model):
    _inherit = "account.journal"

    allow_account_transfer = fields.Boolean(
        'Allow Account Transfer?',
        default=True,
        help='Set if this journals can be used on account transfers'
        )
