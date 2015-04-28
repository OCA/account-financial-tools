# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2013-2015 Noviat nv/sa (www.noviat.com).
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models
from lxml import etree


class account_move_line(models.Model):
    _inherit = 'account.move.line'

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        res = super(account_move_line, self).fields_view_get(
            cr, uid, view_id=view_id, view_type=view_type,
            context=context, toolbar=toolbar, submenu=False)
        if context and 'account_move_line_search_extension' in context \
                and view_type == 'tree':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("/tree")
            for node in nodes:
                if 'editable' in node.attrib:
                    del node.attrib['editable']
            res['arch'] = etree.tostring(doc)
        return res

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        if context and 'account_move_line_search_extension' in context:
            ana_obj = self.pool['account.analytic.account']
            for arg in args:
                if arg[0] == 'analytic_account_id':
                    ana_dom = ['|',
                               ('name', 'ilike', arg[2]),
                               ('code', 'ilike', arg[2])]
                    ana_ids = ana_obj.search(
                        cr, uid, ana_dom, context=context)
                    ana_ids = ana_obj.search(
                        cr, uid, [('id', 'child_of', ana_ids)])
                    arg[2] = ana_ids
                    break
        return super(account_move_line, self).search(
            cr, uid, args, offset=offset, limit=limit, order=order,
            context=context, count=count)
