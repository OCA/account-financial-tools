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


class res_partner(orm.Model):
    """Add related claim office"""
    def _get_claim_office(self, cr, uid, ids, field, args, context=None):
        res = {}
        location_model = self.pool['res.better.zip']
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = False
            domain = [('name', '=', partner.zip),
                      ('city', '=', partner.city),
                      ('claim_office_id', '!=', False)]
            location_id = location_model.search(cr, uid, domain,
                                                order='priority',
                                                limit=1,
                                                context=context)
            if not location_id:
                continue
            loc = location_model.read(cr,
                                      uid,
                                      location_id,
                                      ['claim_office_id'],
                                      load='_classic_write',
                                      context=context)
            res[partner.id] = loc[0]['claim_office_id']
        return res

    _inherit = "res.partner"
    _columns = {
        'claim_office_id': fields.function(_get_claim_office,
                                           type='many2one',
                                           relation='legal.claim.office',
                                           string='Claim office')
    }
