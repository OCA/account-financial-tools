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
from openerp import models, fields


class ResCompany(models.Model):
    """ Add credit control parameters """
    _inherit = 'res.company'

    credit_control_tolerance = fields.Float(string='Credit Control Tolerance',
                                            default=0.1)
    # This is not a property on the partner because we cannot search
    # on fields.property (subclass fields.function).
    credit_policy_id = fields.Many2one('credit.control.policy',
                                       string='Credit Control Policy',
                                       help="The Credit Control Policy used "
                                            "on partners by default. "
                                            "This setting can be overridden"
                                            " on partners or invoices.")
