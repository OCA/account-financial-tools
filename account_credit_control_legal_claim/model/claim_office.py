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


class claim_office(orm.Model):
    """Claim office"""

    _name = "legal.claim.office"
    _columns = {

        'name': fields.char('Name',
                            required=True),

        'locations_ids': fields.one2many('res.better.zip',
                                         'claim_office_id',
                                         'Related zip'),

        'fees_scheme_id': fields.many2one('legal.claim.fees.scheme',
                                          'Fees Scheme',
                                          select=1,
                                          required=True),
        'partner_id': fields.many2one('res.partner',
                                      'Office Address',
                                      required=True),
    }


class better_zip(orm.Model):
    """Add relation to claim office"""

    _inherit = "res.better.zip"
    _columns = {
        'claim_office_id': fields.many2one('legal.claim.office',
                                           'Claim office',
                                           select=True),
    }
