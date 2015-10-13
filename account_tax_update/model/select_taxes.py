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
from openerp.osv import orm, fields


class SelectTaxes(orm.TransientModel):
    _name = 'account.update.tax.select_taxes'
    _description = 'Select the taxes to be updated'
    _rec_name = 'type_tax_use'  # wha'evar

    def save_taxes(self, cr, uid, ids, context=None):
        """
        Create tax lines in the update tax configuration
        based on a user selection of taxes.
        From these taxes, gather their hierarchically related
        other taxes which need to be duplicated to.
        From this gathering, ignore any taxes that might
        have been added by the user earlier on.
        """
        wiz = self.browse(cr, uid, ids[0], context=context)
        # unused tax_pool = self.pool.get('account.tax')
        line_pool = self.pool.get('account.update.tax.config.line')

        def get_root_node(tax):
            if tax.parent_id:
                return get_root_node(tax.parent_id)
            return tax

        def add_tree(tax):
            result = [tax]
            if tax.child_ids:
                for child in tax.child_ids:
                    result += add_tree(child)
            return result

        covered = [x.source_tax_id.id for x in
                   (wiz.config_id.sale_line_ids +
                    wiz.config_id.purchase_line_ids)]
        taxes = []
        for tax in list(set(map(get_root_node, wiz.tax_ids))):
            taxes += add_tree(tax)
        for tax in filter(lambda x: x.id not in covered, taxes):
            line_pool.create(
                cr, uid,
                {'%s_config_id' % wiz.type_tax_use: wiz.config_id.id,
                 'source_tax_id': tax.id,
                 },
                context=context)
        return {'type': 'ir.actions.act_window_close'}

    _columns = {
        'type_tax_use': fields.char(
            'Type tax use', size=16, readonly=True),
        'config_id': fields.many2one(
            'account.update.tax.config',
            'Configuration', readonly=True),
        'tax_ids': fields.many2many(
            'account.tax', 'update_tax_select_account_tax_rel',
            'tax_select_id', 'tax_id',
            string='Taxes'),
        'covered_tax_ids': fields.many2many(
            'account.tax', 'update_tax_select_covered_taxes_rel',
            'tax_select_id', 'tax_id',
            string='Covered taxes'),
    }
