# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2012 Therp BV (<http://therp.nl>).
#    This module copyright (C) 2013 Camptocamp (<http://www.camptocamp.com>).
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


class account_tax(orm.Model):
    _inherit = 'account.tax'

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        # unused res = []
        if context and context.get('tax_real_name'):
            return ((record['id'], record['name']) for record in self.read(
                    cr, uid, ids, ['name'], context=context))
        return super(account_tax, self).name_get(cr, uid, ids, context=context)
