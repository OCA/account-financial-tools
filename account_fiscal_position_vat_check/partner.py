# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Fiscal Position VAT Check module for OpenERP
#    Copyright (C) 2013 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp.osv import orm
from openerp.tools.translate import _


class res_partner(orm.Model):
    _inherit = 'res.partner'

    def fiscal_position_change(self, cr, uid, ids, account_position, vat, customer):
        '''Warning is the fiscal position requires a vat number and the partner
        doesn't have one yet'''
        if account_position and customer and not vat:
            fp = self.pool['account.fiscal.position'].read(
                cr, uid, account_position, ['customer_must_have_vat', 'name'])
            if fp['customer_must_have_vat']:
                return {
                    'warning': {
                        'title': _('Missing VAT number:'),
                        'message': _(
                            "You have set the fiscal position '%s' "
                            "that require the customer to have a VAT number. "
                            "You should add the VAT number of this customer in OpenERP."
                        ) % fp['name']
                    }
                }
        return True
