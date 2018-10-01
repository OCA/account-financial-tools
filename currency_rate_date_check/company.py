# -*- encoding: utf-8 -*-
##############################################################################
#
#    Currency rate date check module for OpenERP
#    Copyright (C) 2012-2013 Akretion (http://www.akretion.com)
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

from openerp.osv import orm, fields

class res_company(orm.Model):
    _inherit = 'res.company'

    _columns = {
        'currency_rate_max_delta': fields.integer(
            'Max Time Delta in Days for Currency Rates',
            help="This is the maximum interval in days between the date associated with the amount to convert and the date of the nearest currency rate available in OpenERP."),
    }

    _defaults = {
        'currency_rate_max_delta': 7,
    }

    _sql_constraints = [
        ('currency_rate_max_delta_positive',
         'CHECK (currency_rate_max_delta >= 0)',
         "The value of the field 'Max Time Delta in Days for Currency Rates' must be positive or 0."),
        ]
