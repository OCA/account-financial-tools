# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models


class account_journal(models.Model):
    _inherit = "account.journal"
    active = fields.Boolean('Active', default=True)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
