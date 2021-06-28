# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models


class ResCompany(models.Model):
    """ Add credit control parameters """
    _inherit = 'res.company'

    credit_control_tolerance = fields.Float(
        string='Credit Control Tolerance',
        default=0.1,
    )
    # This is not a property on the partner because we cannot search
    # on fields.property (subclass fields.function).
    credit_policy_id = fields.Many2one(
        comodel_name='credit.control.policy',
        string='Credit Control Policy',
        help="The Credit Control Policy used on partners by default. "
             "This setting can be overridden on partners or invoices.",
    )
