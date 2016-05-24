# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    permanent_lock_date = fields.Date(
        string="Permanent Lock Date",
        help="Non-revertible closing of accounts prior to and inclusive of "
        "this date. Use it for fiscal year locking instead of ""Lock Date"".")
