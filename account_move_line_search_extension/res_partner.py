# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


class res_partner(models.Model):
    _inherit = 'res.partner'

    def search(self, cr, uid, args,
               offset=0, limit=None, order=None, context=None, count=False):
        if context and 'account_move_line_search_extension' in context:
            args.extend(
                ['|',
                 ('parent_id', '=', False),
                 ('is_company', '=', True),
                 '|',
                 ('active', '=', False),
                 ('active', '=', True)])
        return super(res_partner, self).search(
            cr, uid, args, offset=offset, limit=limit, order=order,
            context=context, count=count)
