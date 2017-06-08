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

from openerp.osv import fields, osv
from openerp.osv.orm import Model
from openerp.tools.translate import _


class product_template(Model):
    _inherit = "product.template"

    _columns = {
        'tax_group_id': fields.many2one(
            'tax.group', 'Tax Group', required=True,
            domain="[('company_id', '=', company_id)]",
            help="Specify the combination of taxes for this product."
            " This field is required. If you dont find the correct Tax"
            " Group, Please create a new one or ask to your account"
            " manager if you don't have the access right."),
    }

    def check_coherent_vals(self, cr, uid, ids, vals, context=None):
        tg_obj = self.pool['tax.group']
        if 'tax_group_id' in vals:
            # update or replace 'taxes_id' and 'supplier_taxes_id'
            tg = tg_obj.browse(cr, uid, vals['tax_group_id'], context=context)
            vals['supplier_taxes_id'] = [[6, 0, [
                x.id for x in tg.supplier_tax_ids]]]
            vals['taxes_id'] = [[6, 0, [
                x.id for x in tg.customer_tax_ids]]]
        elif 'supplier_taxes_id' in vals.keys() or 'taxes_id' in vals.keys():
            if not ids:
                # product template creation mode
                company_id = vals.get('company_id', False)
                supplier_tax_ids = vals.get('supplier_taxes_id', [])
                customer_tax_ids = vals.get('taxes_id', [])
            else:
                # product template Single update mode
                if len(ids) != 1:
                    raise osv.except_osv(
                        _('Unauthorized Update!'),
                        _("You cannot change taxes"
                            " for many product templates"))
                pt = self.browse(cr, uid, ids, context=context)[0]
                company_id = vals.get('company_id', False) or \
                    pt.company_id.id
                if (vals.get('supplier_taxes_id', False) and
                        isinstance(vals.get('supplier_taxes_id')[0], list)):
                    supplier_tax_ids = vals.get('supplier_taxes_id')[0][2]
                else:
                    supplier_tax_ids = [x.id for x in pt.supplier_taxes_id]
                if (vals.get('taxes_id', False) and
                        isinstance(vals.get('taxes_id')[0], list)):
                    customer_tax_ids = vals.get('taxes_id')[0][2]
                else:
                    customer_tax_ids = [x.id for x in pt.taxes_id]
            tg_id = tg_obj.get_or_create(
                cr, uid, [company_id, customer_tax_ids, supplier_tax_ids])
            vals['tax_group_id'] = tg_id

    def create(self, cr, uid, vals, context=None):
        self.check_coherent_vals(cr, uid, False, vals, context=context)
        return super(product_template, self).create(
            cr, uid, vals, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if not isinstance(ids, (tuple, list)):
            ids = [ids]
        self.check_coherent_vals(cr, uid, ids, vals, context=context)
        return super(product_template, self).write(
            cr, uid, ids, vals, context=context)
