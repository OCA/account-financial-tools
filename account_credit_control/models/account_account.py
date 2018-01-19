# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountAccount(models.Model):
    """ Add a link to a credit control policy on account.account """

    _inherit = "account.account"

    credit_control_line_ids = fields.One2many('credit.control.line',
                                              'account_id',
                                              string='Credit Lines',
                                              readonly=True)
