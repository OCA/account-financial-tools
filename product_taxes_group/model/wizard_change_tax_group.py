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

from openerp.osv import fields
from openerp.osv.orm import TransientModel


class wizard_change_tax_group(TransientModel):
    """Wizard to allow to change the Tax Group of products."""
    _name = "wizard.change.tax.group"

    def change_tax_group(self, cr, uid, ids, context=None):
        pt_obj = self.pool['product.template']
        for wctg in self.browse(cr, uid, ids, context=context):
            pt_ids = [
                x.product_tmpl_id.id
                for x in wctg.old_tax_group_id.product_ids]
            pt_obj.write(cr, uid, pt_ids, {
                'tax_group_id': wctg.new_tax_group_id.id}, context=context)
        return {}

    _columns = {
        'old_tax_group_id': fields.many2one(
            'tax.group', 'Old Tax Group', required=True, readonly=True),
        'new_tax_group_id': fields.many2one(
            'tax.group', 'New Tax Group', required=True,
            domain="""[('id', '!=', old_tax_group_id)]"""),
    }

    _defaults = {
        'old_tax_group_id': lambda self, cr, uid, ctx: ctx and ctx.get(
            'active_id', False) or False
    }
