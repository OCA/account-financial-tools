# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#
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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import account

class account_invoice_template(osv.osv):

    _inherit = 'account.document.template'
    _name = 'account.invoice.template'

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'account_id': fields.many2one('account.account', 'Account', required=True),
        'template_line_ids': fields.one2many('account.invoice.template.line', 'template_id', 'Template Lines'),
        'type': fields.selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', required=True ),
        }



account_invoice_template()

class account_invoice_template_line(osv.osv):

    _name = 'account.invoice.template.line'
    _inherit = 'account.document.template.line'

    _columns = {
        'account_id': fields.many2one('account.account', 'Account', required=True, domain=[('type','<>','view'), ('type', '<>', 'closed')]),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', ondelete="cascade"),
        'invoice_line_tax_id': fields.many2many('account.tax', 'account_invoice_template_line_tax', 'invoice_line_id', 'tax_id', 'Taxes', domain=[('parent_id','=',False)]),
        'template_id': fields.many2one('account.invoice.template', 'Template'),
        'product_id': fields.many2one('product.product', 'Product'),
        }

    _sql_constraints = [
        ('sequence_template_uniq', 'unique (template_id,sequence)', 'The sequence of the line must be unique per template !')
    ]

    def product_id_change(self, cr, uid, ids, product_id, type, context=None):
        if context is None:
            context = {}

        result = {}
        if not product_id:
            return {}

        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)

        # name
        result.update({'name': product.name})

        # account
        if type in ('out_invoice','out_refund'):
            a = product.product_tmpl_id.property_account_income.id
            if not a:
                a = product.categ_id.property_account_income_categ.id
        else:
            a = product.product_tmpl_id.property_account_expense.id
            if not a:
                a = product.categ_id.property_account_expense_categ.id

        if a:
            result['account_id'] = a

        # taxes
        if type in ('out_invoice', 'out_refund'):
            tax_id = product.taxes_id and product.taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        else:
            tax_id = product.supplier_taxes_id and product.supplier_taxes_id or (a and self.pool.get('account.account').browse(cr, uid, a, context=context).tax_ids or False)
        taxes = tax_id and map(lambda x: x.id, tax_id) or False
        if type in ('in_invoice', 'in_refund'):
            result.update({'invoice_line_tax_id': taxes})
        else:
            result.update({'invoice_line_tax_id': taxes})

        return {'value': result}

account_invoice_template_line()
