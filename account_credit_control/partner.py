# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2012 Camptocamp SA
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
from openerp.osv.orm import Model, fields


class ResPartner(Model):
    """Add a settings on the credit control policy to use on the partners,
    and links to the credit control lines."""

    _inherit = "res.partner"

    _columns = {
        'credit_policy_id': fields.many2one('credit.control.policy',
                                            'Credit Control Policy',
                                             help=("The Credit Control Policy"
                                                   "used for this partner. This "
                                                   "setting can be forced on the "
                                                   "invoice. If nothing is defined, "
                                                   "it will use the company "
                                                   "setting.")),
        'credit_control_line_ids': fields.one2many('credit.control.line',
                                                   'invoice_id',
                                                   string='Credit Control Lines',
                                                   readonly=True)
    }

