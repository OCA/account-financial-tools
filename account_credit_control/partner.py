# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012-2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from openerp.exceptions import Warning, ValidationError


class ResPartner(models.Model):
    """ Add a settings on the credit control policy to use on the partners,
    and links to the credit control lines.
    """

    _inherit = "res.partner"

    credit_policy_id = fields.Many2one(
        'credit.control.policy',
        string='Credit Control Policy',
        domain="[('account_ids', 'in', property_account_receivable)]",
        help="The Credit Control Policy used for this "
             "partner. This setting can be forced on the "
             "invoice. If nothing is defined, it will use "
             "the company setting.",
    )
    credit_control_line_ids = fields.One2many('credit.control.line',
                                              'partner_id',
                                              string='Credit Control Lines',
                                              readonly=True)

    @api.constrains('credit_policy_id', 'property_account_receivable')
    def _check_credit_policy(self):
        """ Ensure that policy on partner are limited to the account policy """
        for partner in self:
            if (not partner.property_account_receivable or
                    not partner.credit_policy_id):
                continue
            account = partner.property_account_receivable
            policy = partner.credit_policy_id
            try:
                policy.check_policy_against_account(account)
            except Warning as err:
                # constrains should raise ValidationError exceptions
                raise ValidationError(err)
