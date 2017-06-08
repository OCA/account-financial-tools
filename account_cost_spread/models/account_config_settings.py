# -*- coding: utf-8 -*-
# © 2014 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    module_account_cost_spread = fields.Boolean(
        'Cost spreading on Invoices',
        help="""This will allow you to spread the cost of an invoice.
                The module account_cost spread will be installed.""")
