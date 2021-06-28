# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    """ Add a settings on the credit control policy to use on the partners,
    and links to the credit control lines.
    """

    _inherit = "res.partner"

    credit_policy_id = fields.Many2one(
        comodel_name='credit.control.policy',
        string='Credit Control Policy',
        domain="[('account_ids', 'in', property_account_receivable_id)]",
        help="The Credit Control Policy used for this "
             "partner. This setting can be forced on the "
             "invoice. If nothing is defined, it will use "
             "the company setting.",
    )
    credit_control_line_ids = fields.One2many(
        comodel_name='credit.control.line',
        inverse_name='invoice_id',
        string='Credit Control Lines',
        readonly=True,
    )

    @api.constrains('credit_policy_id', 'property_account_receivable_id')
    def _check_credit_policy(self):
        """ Ensure that policy on partner are limited to the account policy """
        # sudo needed for those w/o permission that duplicate records
        for partner in self.sudo():
            if (not partner.property_account_receivable_id or
                    not partner.credit_policy_id):
                continue
            account = partner.property_account_receivable_id
            policy = partner.credit_policy_id
            try:
                policy.check_policy_against_account(account)
            except UserError as err:
                # constrains should raise ValidationError exceptions
                raise ValidationError(err)
