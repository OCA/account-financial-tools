# -*- coding: utf-8 -*-
# Copyright 2009-2016 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from lxml import etree

from openerp import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def fields_view_get(
            self,
            view_id=None,
            view_type='form',
            toolbar=False,
            submenu=False):
        res = super(AccountMoveLine, self).fields_view_get(
            view_id=view_id,
            view_type=view_type,
            oolbar=toolbar,
            submenu=False)
        if self.env.context.get('account_move_line_search_extension') \
                and view_type == 'tree':
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("/tree")
            for node in nodes:
                if 'editable' in node.attrib:
                    del node.attrib['editable']
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def search(
            self,
            args,
            offset=0,
            limit=None,
            order=None,
            count=False):
        if self.env.context.get('account_move_line_search_extension'):
            ana_obj = self.env['account.analytic.account']
            for arg in args:
                if arg[0] == 'analytic_account_id':
                    ana_dom = ['|',
                               ('name', 'ilike', arg[2]),
                               ('code', 'ilike', arg[2])]
                    ana_ids = ana_obj.search(ana_dom)
                    ana_ids = ana_obj.search(
                        [('id', 'child_of', ana_ids)])
                    arg[2] = ana_ids
                    break
        return super(AccountMoveLine, self).search(
            args, offset=offset, limit=limit, order=order, count=count)
