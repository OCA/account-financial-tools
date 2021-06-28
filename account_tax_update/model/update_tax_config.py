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

from datetime import datetime

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.misc import pickle


class UpdateTaxConfig(orm.Model):
    """
    A configuration model to collect taxes to be replaced with
    duplicates, but with a different amount. Once the taxes are
    collected, the following operations can be carried out by
    the user.

    1) generate the target taxes
    2) Update defaults for sales taxes
    3) Update defaults for purchase taxes
    4) Set old taxes inactive
    """
    _name = 'account.update.tax.config'
    _description = 'Update taxes'
    _columns = {
        'name': fields.char(
            'Legacy taxes prefix', size=64, required=True,
            help="The processed taxes will be marked with this name"),
        'log': fields.text(
            'Log', readonly="1"),
        'purchase_line_ids': fields.one2many(
            'account.update.tax.config.line',
            'purchase_config_id',
            'Purchase taxes'),
        'sale_line_ids': fields.one2many(
            'account.update.tax.config.line',
            'sale_config_id',
            'Sales taxes'),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('confirm', 'Confirm'),
             ('update_sales', 'Sales updated'),
             ('update_purchase', 'Purchase updated'),
             ('done', 'Done'),
             ], 'State', readonly=True),
        'default_amount': fields.float(
            'Default new amount', digits=(14, 4),
            help=("Although it is possible to specify a distinct new amount "
                  "per tax, you can set the default value here.")),
        'sale_set_defaults': fields.boolean(
            'Sales tax defaults have been set',
            readonly=True),
        'purchase_set_defaults': fields.boolean(
            'Purchase tax defaults have been set',
            readonly=True),
        'sale_set_inactive': fields.boolean(
            'Sales taxes have been set to inactive',
            readonly=True),
        'purchase_set_inactive': fields.boolean(
            'Purchase taxes have been set to inactive',
            readonly=True),
        'duplicate_tax_code': fields.boolean(
            'Duplicate Tax code linked'),
    }

    _defaults = {
        'state': 'draft',
    }

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique.'),
    ]

    def add_lines(self, cr, uid, ids, context=None):
        """
        Call the wizard that adds configuration lines
        """
        if not ids:
            return
        if isinstance(ids, (int, float)):
            ids = [ids]
        wizard_obj = self.pool.get('account.update.tax.select_taxes')
        config = self.browse(cr, uid, ids[0], context=context)
        if not context or not context.get('type_tax_use'):
            raise orm.except_orm(
                _("Error"),
                _("Can not detect tax use type"))
        covered_tax_ids = [
            x.source_tax_id.id
            for x in config['purchase_line_ids'] + config['sale_line_ids']
        ]

        res_id = wizard_obj.create(
            cr, uid, {
                'config_id': ids[0],
                'type_tax_use': context['type_tax_use'],
                'covered_tax_ids': [(6, 0, covered_tax_ids)],
            },
            context=context)
        local_context = context.copy()
        local_context['active_id'] = res_id

        return {
            'name': wizard_obj._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard_obj._name,
            'domain': [],
            'context': context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id,
            'nodestroy': True,
        }

    def confirm(self, cr, uid, ids, context=None):
        """
        Set the configuration to confirmed, so that no new
        taxes can be added. Create the duplicate taxes,
        rename the legacy taxes and recreate the hierarchical
        structure. Construct the fiscal position tax mappings.
        """
        config = self.browse(cr, uid, ids[0], context=None)
        tax_pool = self.pool.get('account.tax')
        tax_code_pool = self.pool.get('account.tax.code')
        line_pool = self.pool.get('account.update.tax.config.line')
        tax_map = {}
        log = (config.log or '') + (
            "\n*** %s: Confirmed with the following taxes:\n" %
            datetime.now().ctime())
        for line in config.sale_line_ids + config.purchase_line_ids:
            log += " - %s (%s)\n" % (
                line.source_tax_id.name,
                line.source_tax_id.description
            )
            # Switch names around, not violating the uniqueness constraint
            tax_old_name = line.source_tax_id.name
            tax_pool.write(
                cr, uid, line.source_tax_id.id,
                {'name': '[%s] %s' % (config.name, tax_old_name)},
                context=context)
            if line.source_tax_id.amount in [1.0, -1.0, 0]:
                amount_new = line.source_tax_id.amount
            else:
                amount_new = config.default_amount or line.source_tax_id.amount
            # 6.0 messes up the name change with copy + write, while
            # 6.1 throws name uniqueness constraint violation
            # So jumping some hoops with rewriting the new name
            # We will check if we need to dupliace
            cp_base_code_id = False
            cp_ref_base_code_id = False
            cp_tax_code_id = False
            cp_ref_tax_code_id = False
            if config.duplicate_tax_code:
                if line.source_tax_id.base_code_id:
                    cp_base_code_id = tax_code_pool.copy(
                        cr, uid,
                        line.source_tax_id.base_code_id.id
                    )
                    rename_old = '[%s] %s' % (
                        config.name,
                        line.source_tax_id.base_code_id.name
                    )
                    tax_code_pool.write(cr, uid,
                                        line.source_tax_id.base_code_id.id,
                                        {'name': rename_old})
                if line.source_tax_id.tax_code_id:
                    cp_tax_code_id = tax_code_pool.copy(
                        cr, uid,
                        line.source_tax_id.tax_code_id.id
                    )
                    rename_old = '[%s] %s' % (
                        config.name,
                        line.source_tax_id.tax_code_id.name
                    )
                    tax_code_pool.write(cr, uid,
                                        line.source_tax_id.tax_code_id.id,
                                        {'name': rename_old})
                if line.source_tax_id.ref_base_code_id:
                    # Check if with have the same tax code for base_code_id
                    if (line.source_tax_id.ref_base_code_id.id ==
                            line.source_tax_id.base_code_id.id):
                        cp_ref_base_code_id = cp_base_code_id
                    else:
                        cp_ref_base_code_id = tax_code_pool.copy(
                            cr, uid,
                            line.source_tax_id.ref_base_code_id.id
                        )
                        rename_old = '[%s] %s' % (
                            config.name,
                            line.source_tax_id.ref_base_code_id.name
                        )
                        tax_code_pool.write(
                            cr, uid,
                            line.source_tax_id.ref_base_code_id.id,
                            {'name': rename_old}
                        )
                if line.source_tax_id.ref_tax_code_id:
                    if (line.source_tax_id.ref_tax_code_id.id ==
                            line.source_tax_id.tax_code_id.id):
                        cp_ref_tax_code_id = cp_tax_code_id
                    else:
                        cp_ref_tax_code_id = tax_code_pool.copy(
                            cr, uid,
                            line.source_tax_id.ref_tax_code_id.id
                        )
                        rename_old = '[%s] %s' % (
                            config.name,
                            line.source_tax_id.ref_tax_code_id.name
                        )
                        tax_code_pool.write(
                            cr, uid,
                            line.source_tax_id.ref_tax_code_id.id,
                            {'name': rename_old}
                        )
            else:
                cp_base_code_id = (line.source_tax_id.base_code_id and
                                   line.source_tax_id.base_code_id.id or
                                   False)
                cp_ref_base_code_id = (
                    line.source_tax_id.ref_base_code_id and
                    line.source_tax_id.ref_base_code_id.id or
                    False
                )
                cp_tax_code_id = (line.source_tax_id.tax_code_id and
                                  line.source_tax_id.tax_code_id.id or
                                  False)
                cp_ref_tax_code_id = (line.source_tax_id.ref_tax_code_id and
                                      line.source_tax_id.ref_tax_code_id.id or
                                      False)

            target_tax_id = tax_pool.copy(
                cr, uid, line.source_tax_id.id,
                {
                    'name': '[update, %s] %s' % (config.name, tax_old_name),
                    'amount': amount_new,
                    'parent_id': False,
                    'child_ids': [(6, 0, [])],
                },
                context=context
            )
            tax_pool.write(
                cr, uid, target_tax_id,
                {'name': tax_old_name,
                 'base_code_id': cp_base_code_id,
                 'ref_base_code_id': cp_ref_base_code_id,
                 'tax_code_id': cp_tax_code_id,
                 'ref_tax_code_id': cp_ref_tax_code_id},
                context=context
            )
            tax_map[line.source_tax_id.id] = target_tax_id
            line_pool.write(
                cr, uid, line.id,
                {'target_tax_id': target_tax_id}, context=context)
        # Map the parent_id
        # First, rebrowse the config
        # (as browse_record.refresh() is not available in 6.0)
        config = self.browse(cr, uid, ids[0], context=None)
        for line in config.sale_line_ids + config.purchase_line_ids:
            if line.source_tax_id.parent_id:
                tax_pool.write(
                    cr, uid, line.target_tax_id.id,
                    {'parent_id': tax_map[line.source_tax_id.parent_id.id]},
                    context=context)
        # Map fiscal positions
        fp_tax_pool = self.pool.get('account.fiscal.position.tax')
        fp_tax_ids = fp_tax_pool.search(
            cr, uid, [('tax_src_id', 'in', tax_map.keys())], context=context)
        fp_taxes = fp_tax_pool.browse(cr, uid, fp_tax_ids, context=context)
        for fp_tax in fp_taxes:
            new_fp_tax_id = fp_tax_pool.copy(
                cr, uid, fp_tax.id,
                {'tax_src_id': tax_map[fp_tax.tax_src_id.id],
                 'tax_dest_id': tax_map.get(
                     fp_tax.tax_dest_id.id, fp_tax.tax_dest_id.id)},
                context=context)
            new_fp_tax = fp_tax_pool.browse(
                cr, uid, new_fp_tax_id, context=context)
            log += ("\nCreate new tax mapping on position %s:\n"
                    "%s (%s)\n"
                    "=> %s (%s)\n" % (
                        new_fp_tax.position_id.name,
                        new_fp_tax.tax_src_id.name,
                        new_fp_tax.tax_src_id.description,
                        new_fp_tax.tax_dest_id.name,
                        new_fp_tax.tax_dest_id.description,
                    ))
        self.write(
            cr, uid, ids[0],
            {'state': 'confirm', 'log': log}, context=context)
        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': context,
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'nodestroy': True,
        }

    def set_defaults(self, cr, uid, ids, context=None):
        if not context or not context.get('type_tax_use'):
            raise orm.except_orm(
                _("Error"),
                _("Can not detect tax use type"))
        local_context = context.copy()
        local_context['active_test'] = False
        config = self.browse(cr, uid, ids[0], context=None)
        tax_lines = config['%s_line_ids' % context['type_tax_use']]
        tax_map = dict([(x.source_tax_id.id, x.target_tax_id.id)
                        for x in tax_lines])
        ir_values_pool = self.pool.get('ir.values')
        log = (config.log or '') + (
            "\n*** %s: Writing default %s taxes:\n" % (
                datetime.now().ctime(),
                context['type_tax_use']))

        def update_defaults(model_name, field_name, column):
            log = ''
            if column._obj == 'account.tax':
                values_ids = ir_values_pool.search(
                    cr, uid,
                    [('key', '=', 'default'),
                     ('model', '=', model_name),
                     ('name', '=', field_name)],
                    context=local_context)
                for value in ir_values_pool.browse(
                        cr, uid, values_ids, context=context):
                    val = False
                    write = False
                    try:
                        # Currently, value_unpickle from ir_values
                        # fails as it feeds unicode to pickle.loads()
                        val = pickle.loads(str(value.value))
                    except:
                        continue
                    if isinstance(val, (int, long)) and val in tax_map:
                        write = True
                        new_val = tax_map[val]
                    elif isinstance(val, list) and val:
                        new_val = []
                        for i in val:
                            if i in tax_map:
                                write = True
                            new_val.append(tax_map.get(i, i))
                    if write:
                        log += "Default (%s => %s) for %s,%s\n" % (
                            val, new_val, model_name, field_name)
                        ir_values_pool.write(
                            cr, uid, value.id,
                            {'value_unpickle': new_val}, context=context)
            return log

        model_pool = self.pool.get('ir.model')
        model_ids = model_pool.search(cr, uid, [], context=context)
        models = model_pool.read(
            cr, uid, model_ids, ['model'], context=context)
        pool_models_items = [(x['model'], self.pool.get(
            x['model'])) for x in models]
        # 6.1: self.pool.models.items():
        for model_name, model in pool_models_items:
            if model:
                for field_name, column in model._columns.items():
                    log += update_defaults(model_name, field_name, column)
                for field_name, field_tuple in \
                        model._inherit_fields.iteritems():
                    if len(field_tuple) >= 3:
                        column = field_tuple[2]
                        log += update_defaults(model_name, field_name, column)

        log += "\nReplacing %s taxes on accounts and products\n" % (
            context['type_tax_use'])
        for (model, field) in [
            # make this a configurable list of ir_model_fields one day?
                ('account.account', 'tax_ids'),
                ('product.product', 'supplier_taxes_id'),
                ('product.product', 'taxes_id'),
                ('product.template', 'supplier_taxes_id'),
                ('product.template', 'taxes_id')]:
            pool = self.pool.get(model)
            obj_ids = pool.search(
                cr, uid, [(field, 'in', tax_map.keys())],
                context=local_context)
            for obj in pool.read(
                    cr, uid, obj_ids, [field], context=context):
                new_val = []
                write = False
                for i in obj[field]:
                    if i in tax_map:
                        write = True
                    new_val.append(tax_map.get(i, i))
                if write:
                    pool.write(
                        cr, uid, obj['id'],
                        {field: [(6, 0, new_val)]},
                        context=context)
                    log += "Value (%s => %s) for %s,%s,%s\n" % (
                        obj[field], new_val, model, field, obj['id'])
        self.write(
            cr, uid, ids[0],
            {'log': log, '%s_set_defaults' % context['type_tax_use']: True},
            context=context)

        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': context,
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'nodestroy': True,
        }

    def set_inactive(self, cr, uid, ids, context=None):
        if not context or not context.get('type_tax_use'):
            raise orm.except_orm(
                _("Error"),
                _("Can not detect tax use type"))
        config = self.browse(cr, uid, ids[0], context=None)
        tax_lines = config['%s_line_ids' % context['type_tax_use']]
        tax_pool = self.pool.get('account.tax')
        tax_ids = tax_pool.search(
            cr, uid,
            [('id', 'in',
              [x.source_tax_id.id for x in tax_lines])],
            context=context)
        tax_pool.write(
            cr, uid, tax_ids, {'active': False}, context=context)
        log = (config.log or '') + (
            "\n*** %s: Setting %s %s taxes inactive\n" % (
                datetime.now().ctime(),
                len(tax_ids),
                context['type_tax_use']))
        self.write(
            cr, uid, ids[0],
            {'log': log, '%s_set_inactive' % context['type_tax_use']: True},
            context=context)

        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': context,
            'type': 'ir.actions.act_window',
            'res_id': ids[0],
            'nodestroy': True,
        }


class UpdateTaxConfigLine(orm.Model):
    _name = 'account.update.tax.config.line'
    _description = "Tax update configuration lines"
    _rec_name = 'source_tax_id'  # Wha'evuh

    def _get_config_field(
            self, cr, uid, ids, field, args, context=None):
        # Retrieve values of the associated config_id
        # either sale or purchase
        result = dict([(x, False) for x in ids or []])
        for x in self.browse(cr, uid, ids, context=context):
            config = x['sale_config_id'] or x['purchase_config_id']
            if config:
                result[x.id] = config[field]
        return result

    _columns = {
        'purchase_config_id': fields.many2one(
            'account.update.tax.config',
            'Configuration'),
        'sale_config_id': fields.many2one(
            'account.update.tax.config',
            'Configuration'),
        'source_tax_id': fields.many2one(
            'account.tax', 'Source tax',
            required=True),
        'source_tax_description': fields.related(
            'source_tax_id', 'description',
            type='char', size=32,
            string="Old tax code"),
        'target_tax_id': fields.many2one(
            'account.tax', 'Target tax'),
        'target_tax_description': fields.related(
            'target_tax_id', 'description',
            type='char', size=32,
            string="New tax code"),
        'amount_old': fields.related(
            'source_tax_id', 'amount',
            type='float', digits=(14, 4),
            string='Old amount', readonly=True),
        'amount_new': fields.related(
            'target_tax_id', 'amount',
            type='float', digits=(14, 4),
            string='New amount'),
        'state': fields.function(
            _get_config_field, 'state', method=True,
            type='char', size=16, string='State'),
    }
