# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 ACSONE SA/NV (http://acsone.eu)
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


class AccountTaxCode(models.Model):
    _inherit = 'account.tax.code'

    active = fields.Boolean('Active', default=True)

    def _sum(self, cr, uid, ids, name, args, context, where='',
             where_params=()):
        try:
            return super(AccountTaxCode, self)._sum(
                cr, uid, ids, name, args, context, where=where,
                where_params=where_params)
        except:
            cr.rollback()
            return dict.fromkeys(ids, 0.0)
