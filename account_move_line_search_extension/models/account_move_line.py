# Copyright 2009-2019 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from lxml import etree

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if 'account_move_line_search_extension' in self.env.context:
            for arg in args:

                if arg[0] == 'amount_search' and len(arg) == 3:
                    digits = self.env['decimal.precision'].precision_get(
                        'Account')
                    val = str2float(arg[2])
                    if val is not None:
                        if arg[2][0] in ['+', '-']:
                            f1 = 'balance'
                            f2 = 'amount_currency'
                        else:
                            f1 = 'abs(balance)'
                            f2 = 'abs(amount_currency)'
                            val = abs(val)
                        query = (
                            "SELECT id FROM account_move_line "
                            "WHERE round({0} - {2}, {3}) = 0.0 "
                            "OR round({1} - {2}, {3}) = 0.0"
                        ).format(f1, f2, val, digits)
                        self.env.cr.execute(query)
                        res = self.env.cr.fetchall()
                        ids = res and [x[0] for x in res] or [0]
                        arg[0] = 'id'
                        arg[1] = 'in'
                        arg[2] = ids
                    else:
                        arg[0] = 'id'
                        arg[1] = '='
                        arg[2] = 0
                    break

            for arg in args:
                if arg[0] == 'analytic_account_search':
                    ana_dom = ['|',
                               ('name', 'ilike', arg[2]),
                               ('code', 'ilike', arg[2])]
                    arg[0] = 'analytic_account_id'
                    arg[2] = self.env['account.analytic.account'].search(
                        ana_dom).ids
                    break

        return super().search(
            args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if (self.env.context.get('account_move_line_search_extension')
                and view_type == 'form'):
            doc = etree.XML(res['arch'])
            form = doc.xpath("/form")
            for node in form:
                node.set('edit', 'false')
                node.set('create', 'false')
                node.set('delete', 'false')
            res['arch'] = etree.tostring(doc)
        return res

    @api.model
    def get_amlse_render_dict(self):
        """
        The result of this method is merged into the
        action context for the Qweb rendering.
        """
        render_dict = {}
        for group in self._get_amlse_groups():
            if self.env.user.has_group(group):
                render_dict[group.replace('.', '_')] = True
        return render_dict

    def _get_amlse_groups(self):
        return [
            'analytic.group_analytic_accounting',
        ]


def str2float(val):
    pattern = re.compile('[0-9]')
    dot_comma = pattern.sub('', val)
    if dot_comma and dot_comma[-1] in ['.', ',']:
        decimal_separator = dot_comma[-1]
    else:
        decimal_separator = False
    if decimal_separator == '.':
        val = val.replace(',', '')
    else:
        val = val.replace('.', '').replace(',', '.')
    try:
        return float(val)
    except Exception:
        return None
