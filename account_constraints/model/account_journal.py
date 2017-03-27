# -*- coding: utf-8 -*-
# © 2012, Joel Grand-Guillaume, Camptocamp SA.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'
    allow_date_fy = fields.Boolean(string='Check Date in Fiscal Year',
                                   help='If set to True then do not '
                                        'accept the entry if '
                                        'the entry date is not into '
                                        'the fiscal year dates',
                                   default=True)
