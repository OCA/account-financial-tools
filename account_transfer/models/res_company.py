# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import models, fields


class res_company(models.Model):

    _inherit = 'res.company'

    transfer_account_id = fields.Many2one(
        'account.account',
        'Transfer Account',
        domain="[('company_id', '=', id), "
        "('type', 'not in', ('view', 'closed', 'consolidation'))]",
        help="Account used on transfers between Bank and Cash Journals"
        )
