# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 Numérigraphe SARL.
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

from openerp.osv import fields, orm


class res_company(orm.Model):
    """Replace the company's fields for SIRET/RC with the partner's"""
    _inherit = 'res.company'

    def _get_partner_change(self, cr, uid, ids, context=None):
        return self.pool['res.company'].search(
            cr, uid, [('partner_id', 'in', ids)], context=context)

    _columns = {
        'siret': fields.related(
            'partner_id', 'siret', type='char', string='SIRET', store={
                'res.partner': (_get_partner_change, ['siren', 'nic'], 20),
                'res.company': (lambda self, cr, uid, ids, c={}:
                                ids, ['partner_id'], 20), }),
        'company_registry': fields.related(
            'partner_id', 'company_registry', type='char',
            string='Company Registry', store={
                'res.partner': (_get_partner_change, ['company_registry'], 20),
                'res.company': (lambda self, cr, uid, ids, c={}:
                                ids, ['partner_id'], 20), })
    }
