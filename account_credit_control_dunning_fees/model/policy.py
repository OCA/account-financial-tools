# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from openerp.osv import orm, fields


class credit_control_policy(orm.Model):
    """ADD dunning fees fields"""

    _inherit = "credit.control.policy.level"
    _columns = {'dunning_product_id': fields.many2one('product.product',
                                                      'Fees Product'),
                'dunning_fixed_amount': fields.float('Fees Fixed Amount'),
                'dunning_currency_id': fields.many2one('res.currency',
                                                       'Fees currency'),
                # planned type are fixed, percent, compound
                'dunning_fees_type': fields.selection([('fixed', 'Fixed')])}

    _defaults = {'dunning_fees_type': 'fixed'}
