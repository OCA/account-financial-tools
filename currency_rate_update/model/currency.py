# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2009-TODAY CLEARCORP S.A. (<http://clearcorp.co.cr>).
#    @author Glen Sojo
#
#    Abstract class to fetch rates from Central Bank of Costa Rica
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


class ResCurrency(models.Model):

    _inherit = 'res.currency'

    indicator = fields.Integer('Indicator', help='Central Bank of Costa Rica '
                               'indicator identifier for sale and purchase rates. Valid indicators '
                               'are shown in the webservice documentation at http://www.bccr.fi.cr/')
