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


class ResCompany(Model):

    _inherit = 'res.company'

    _columns = {
        'credit_control_tolerance': fields.float('Credit Control Tolerance'),
        # This is not a property on the partner because we cannot search
        # on fields.property (subclass fields.function).
        'credit_policy_id': fields.many2one(
            'credit.control.policy',
            'Credit Control Policy',
             help=("The Credit Control Policy used on partners by default. This "
                   "setting can be overriden on partners or invoices.")),
    }

    _defaults = {"credit_control_tolerance": 0.1}

