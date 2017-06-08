# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Taxes Group module for Odoo
#    Copyright (C) 2014 -Today GRAP (http://www.grap.coop)
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
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

import logging

from openerp.osv import fields, osv
from openerp.osv.orm import Model
from openerp import SUPERUSER_ID
from openerp.tools.translate import _

_logger = logging.getLogger(__name__)


class tax_group(Model):
    """Group of customer and supplier taxes.
    This group is linked to a product to select a group of taxes in one
    time."""
    _name = "tax.group"
    _description = "Tax Group"
    _MAX_LENGTH_NAME = 256

    # Functional Fields Section
    def _get_product_qty(self, cr, uid, ids, name, args, context=None):
        res = dict([(id, 0) for id in ids])
        pp_obj = self.pool['product.product']
        result = pp_obj.read_group(
            cr, uid, [
                ('tax_group_id', 'in', ids), '|', ('active', '=', False),
                ('active', '=', True)],
            ['tax_group_id'], ['tax_group_id'])
        for x in result:
            res[x['tax_group_id'][0]] = x['tax_group_id_count']
        return res

    def _get_product_ids(self, cr, uid, ids, name, args, context=None):
        res = dict([(id, []) for id in ids])
        pp_obj = self.pool['product.product']
        for id in ids:
            pp_ids = pp_obj.search(
                cr, uid, [
                    ('tax_group_id', '=', id), '|', ('active', '=', False),
                    ('active', '=', True)], context=context)
            res[id] = pp_ids
        return res

    _columns = {
        'name': fields.char(
            'Name', size=_MAX_LENGTH_NAME, required=True, select=True),
        'company_id': fields.many2one(
            'res.company', 'Company', help="Specify a company if you want to"
            "define this Tax Group only for specific company. Otherwise, "
            "this tax group will be available for all companies."),
        'active': fields.boolean(
            'Active', help="If unchecked, it will allow you to hide the tax"
            " group without removing it."),
        'product_ids': fields.function(
            _get_product_ids, type='one2many', relation='product.product',
            string='Products'),
        'product_qty': fields.function(
            _get_product_qty, type='integer',
            string='Products Quantity'),
        'supplier_tax_ids': fields.many2many(
            'account.tax', 'product_supplier_tax_rel',
            'prod_id', 'tax_id', 'Supplier Taxes', domain="""[
                ('company_id', '=', company_id),
                ('parent_id', '=', False),
                ('type_tax_use', 'in', ['purchase', 'all'])]"""),
        'customer_tax_ids': fields.many2many(
            'account.tax', 'product_customer_tax_rel',
            'prod_id', 'tax_id', 'Customer Taxes', domain="""[
                ('company_id', '=', company_id),
                ('parent_id', '=', False),
                ('type_tax_use', 'in', ['sale', 'all'])]"""),
    }

    _defaults = {
        'active': True,
        'company_id': lambda s, cr, uid, c: (
            s.pool.get('res.users')._get_company(cr, uid, context=c)),
    }

    # Overload Section
    def write(self, cr, uid, ids, vals, context=None):
        pt_obj = self.pool['product.template']
        res = super(tax_group, self).write(
            cr, uid, ids, vals, context=context)
        if 'supplier_tax_ids' in vals or 'customer_tax_ids' in vals:
            for tg in self.browse(cr, uid, ids, context=context):
                pt_obj.write(
                    cr, uid, [x.product_tmpl_id.id for x in tg.product_ids],
                    {'tax_group_id': tg.id}, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        for tg in self.browse(cr, uid, ids, context=context):
            if tg.product_qty != 0:
                raise osv.except_osv(
                    _('Non Empty Tax Group!'),
                    _("""You cannot delete The tax Group '%s' because"""
                        """ it contents %s products. Please move products"""
                        """ to another Tax Group.""") % (
                            tg.name, tg.product_qty))
        return super(tax_group, self).unlink(cr, uid, ids, context=context)

    # Custom Section
    def get_or_create(self, cr, uid, values, context=None):
        at_obj = self.pool['account.tax']
        # Search for existing Tax Group
        tg_ids = self.search(
            cr, uid, ['|', ('active', '=', False), ('active', '=', True)],
            context=context)
        for tg in self.browse(cr, uid, tg_ids, context=context):
            if (tg.company_id.id == values[0] and
                sorted([x.id for x in tg.customer_tax_ids]) == values[1] and
                    sorted([x.id for x in tg.supplier_tax_ids]) == values[2]):
                return tg.id

        # create new Tax Group if not found
        if len(values[1]) == 0 and len(values[2]) == 0:
            name = _('No taxes')
        elif len(values[2]) == 0:
            name = _('No Purchase Taxes - Customer Taxes: ')
            for tax in at_obj.browse(cr, uid, values[1], context=context):
                name += tax.description and tax.description or tax.name
                name += ' + '
            name = name[:-3]
        elif len(values[1]) == 0:
            name = _('Purchase Taxes: ')
            for tax in at_obj.browse(cr, uid, values[2], context=context):
                name += tax.description and tax.description or tax.name
                name += ' + '
            name = name[:-3]
            name += _('- No Customer Taxes')
        else:
            name = _('Purchase Taxes: ')
            for tax in at_obj.browse(cr, uid, values[2], context=context):
                name += tax.description and tax.description or tax.name
                name += ' + '
            name = name[:-3]
            name += _(' - Customer Taxes: ')
            for tax in at_obj.browse(cr, uid, values[1], context=context):
                name += tax.description and tax.description or tax.name
                name += ' + '
            name = name[:-3]
        name = name[:self._MAX_LENGTH_NAME] \
            if len(name) > self._MAX_LENGTH_NAME else name
        return self.create(
            cr, uid, {
                'name': name,
                'company_id': values[0],
                'customer_tax_ids': [(6, 0, values[1])],
                'supplier_tax_ids': [(6, 0, values[2])]}, context=context)

    def init(self, cr):
        """Generate Tax Groups for each combinations of Tax Group set
        in product"""
        uid = SUPERUSER_ID
        pt_obj = self.pool['product.template']
        tg_obj = self.pool['tax.group']

        # Get all Tax Group (if update process)
        list_res = {}
        tg_ids = tg_obj.search(
            cr, uid, ['|', ('active', '=', False), ('active', '=', True)])
        tg_list = tg_obj.browse(cr, uid, tg_ids)
        for tg in tg_list:
            list_res[tg.id] = [
                tg.company_id and tg.company_id.id or False,
                sorted([x.id for x in tg.customer_tax_ids]),
                sorted([x.id for x in tg.supplier_tax_ids])]

        # Get all product template without tax group defined
        pt_ids = pt_obj.search(cr, uid, [('tax_group_id', '=', False)])

        pt_list = pt_obj.browse(cr, uid, pt_ids)
        counter = 0
        total = len(pt_list)
        # Associate product template to existing or new tax group
        for pt in pt_list:
            counter += 1
            res = [
                pt.company_id and pt.company_id.id or False,
                sorted([x.id for x in pt.taxes_id]),
                sorted([x.id for x in pt.supplier_taxes_id])]
            if res not in list_res.values():
                _logger.info(
                    """create new Tax Group. Product templates"""
                    """ managed %s/%s""" % (counter, total))
                tg_id = self.get_or_create(cr, uid, res, context=None)
                list_res[tg_id] = res
                # associate product template to the new Tax Group
                pt_obj.write(cr, uid, [pt.id], {'tax_group_id': tg_id})
            else:
                # associate product template to existing Tax Group
                pt_obj.write(cr, uid, [pt.id], {
                    'tax_group_id': list_res.keys()[
                        list_res.values().index(res)]})
