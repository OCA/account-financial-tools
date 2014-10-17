# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Fiscal Position VAT Check module for Odoo
#    Copyright (C) 2013-2014 Akretion (http://www.akretion.com)
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

from openerp import models, api, _


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def fiscal_position_change(
            self, account_position_id, vat, customer):
        '''Warning if the fiscal position requires a VAT number and the
        partner doesn't have one yet'''
        if account_position_id and customer and not vat:
            fp = self.env['account.fiscal.position'].browse(
                account_position_id)
            if fp.customer_must_have_vat:
                return {
                    'warning': {
                        'title': _('Missing VAT number:'),
                        'message': _(
                            "You have set the fiscal position '%s' "
                            "that require the customer to have a VAT number, "
                            "but the VAT number is missing.") % fp.name
                    }
                }
        return True
