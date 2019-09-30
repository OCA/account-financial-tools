# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    credit_control_notes = fields.Char()
    credit_control_date = fields.Date(
        string='Credit Control Ignore Before',
        help="If filled in, specify a pivot date to ignore moves before for "
             "credit control"
    )
