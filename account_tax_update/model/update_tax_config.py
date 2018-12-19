# -*- coding: utf-8 -*-

from openerp import api, models, fields, _
from openerp.exceptions import ValidationError
from openerp.tools import pickle


class UpdateTaxConfig(models.Model):
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

    name = fields.Char(
        'Legacy taxes prefix', size=64, required=True,
        help="The processed taxes will be marked with this name")
    log = fields.Text(
        'Log', readonly="1")
    purchase_line_ids = fields.One2many(
        'account.update.tax.config.line',
        'purchase_config_id',
        'Purchase taxes')
    sale_line_ids = fields.One2many(
        'account.update.tax.config.line',
        'sale_config_id',
        'Sales taxes')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('confirm', 'Confirm'),
         ('update_sales', 'Sales updated'),
         ('update_purchase', 'Purchase updated'),
         ('done', 'Done'),
         ], 'State', readonly=True, default='draft')
    sale_set_defaults = fields.Boolean(
        'Sales tax defaults have been set',
        readonly=True)
    purchase_set_defaults = fields.Boolean(
        'Purchase tax defaults have been set',
        readonly=True)
    sale_set_inactive = fields.Boolean(
        'Sales taxes have been set to inactive',
        readonly=True)
    purchase_set_inactive = fields.Boolean(
        'Purchase taxes have been set to inactive',
        readonly=True)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Name must be unique.'),
    ]

    @api.multi
    def add_lines(self):
        """
        Call the wizard that adds configuration lines
        """
        wizard_obj = self.env['account.update.tax.select_taxes']
        if not self.env.context or not self.env.context.get('type_tax_use'):
            raise ValidationError(_("Can not detect tax use type"))
        # all taxes involved
        covered_tax_ids = [
            x.source_tax_id.id
            for x in self['purchase_line_ids'] + self['sale_line_ids']
        ]
        if not covered_tax_ids:
            covered_tax_ids = []
        res_id = wizard_obj.create(
            {
                'config_id': self.ids[0],
                'type_tax_use': self.env.context['type_tax_use'],
                'covered_tax_ids': [(6, 0, covered_tax_ids)],
            })
        local_context = self.env.context.copy()
        local_context['active_id'] = res_id.id
        local_context['type_tax_use'] = res_id.type_tax_use
        return {
            'name': wizard_obj._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard_obj._name,
            'domain': [],
            'context': local_context,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
            'nodestroy': True,
        }

    @api.multi
    def confirm(self):
        """
        Set the configuration to confirmed, so that no new
        taxes can be added. Create the duplicate taxes,
        rename the legacy taxes and recreate the hierarchical
        structure. Construct the fiscal position tax mappings.
        """
        tax_map = {}
        log = (self.log or '') + (
            "\n*** %s: Confirmed with the following taxes:\n" %
            fields.Datetime.now())
        for line in self.sale_line_ids + self.purchase_line_ids:
            log += " - %s (%s)\n" % (
                line.source_tax_id.name,
                line.source_tax_id.description
            )
            # Switch names around, not violating the uniqueness constraint
            old_name = line.source_tax_id.name
            line.source_tax_id.write({
                'name': "[replaced in %s] %s" % (
                    self.name, line.source_tax_id.name)})
            res = line.source_tax_id.copy_data()
            res[0].update({
                'name': '[%s] %s' % (self.name, old_name),
                'amount': line.amount_new or line.amount_old,
                'description': line.target_tax_description or
                line.source_tax_description,
                'children_tax_ids': [(6, 0, [])],
            })
            target_tax_id = self.env['account.tax'].create(res[0])

            tax_map[line.source_tax_id.id] = target_tax_id.id
            line.write({'target_tax_id': target_tax_id.id})
        for line in self.sale_line_ids + self.purchase_line_ids:
            if line.source_tax_id.children_tax_ids:
                line.target_tax_id.write(
                    {'children_tax_ids': [(6, 0, [
                        tax_map[x] for x in
                        line.source_tax_id.children_tax_ids.ids])]})
        # Map fiscal positions
        fp_tax_model = self.env['account.fiscal.position.tax']
        fp_taxes = fp_tax_model.search(
            [('tax_src_id', 'in', tax_map.keys())])
        for fp_tax in fp_taxes:
            new_fp_tax = fp_tax.copy(
                {'tax_src_id': tax_map[fp_tax.tax_src_id.id],
                 'tax_dest_id': tax_map.get(
                     fp_tax.tax_dest_id.id, fp_tax.tax_dest_id.id)},)
            log += ("\nCreate new tax mapping on position %s:\n"
                    "%s (%s)\n"
                    "=> %s (%s)\n" % (
                        new_fp_tax.position_id.name,
                        new_fp_tax.tax_src_id.name,
                        new_fp_tax.tax_src_id.description,
                        new_fp_tax.tax_dest_id.name,
                        new_fp_tax.tax_dest_id.description,
                    ))
        self[0].write(
            {'state': 'confirm', 'log': log})
        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_id': self[0].id,
            'nodestroy': True,
        }

    @api.multi
    def set_defaults(self):
        if not self.env.context or not self.env.context.get('type_tax_use'):
            raise ValidationError(_("Can not detect tax use type"))
        local_context = self.env.context.copy()
        local_context['active_test'] = False
        tax_lines = self['%s_line_ids' % self.env.context['type_tax_use']]
        tax_map = dict([(x.source_tax_id.id, x.target_tax_id.id)
                        for x in tax_lines])
        ir_values_model = self.env['ir.values']
        log = (self.log or '') + (
            "\n*** %s: Writing default %s taxes:\n" % (
                fields.Datetime.now(),
                self.env.context['type_tax_use']))

        def update_defaults(model_name, field_name, column):
            log = ''
            if column._obj == 'account.tax':
                values_ids = ir_values_model.with_context(
                    local_context).search(
                        [('key', '=', 'default'),
                         ('model', '=', model_name),
                         ('name', '=', field_name)])
                for value in values_ids:
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
                        value.write({'value_unpickle': new_val})
            return log

        model_model = self.env['ir.model']
        model_ids = model_model.search([])
        models = model_ids.read(['model'])
        models_items = [(x['model'], self.env[x['model']]) for x in models]
        for model_name, model in models_items:
            if model:
                for field_name, column in model._columns.items():
                    log += update_defaults(model_name, field_name, column)
                for field_name, field_tuple in \
                        model._inherit_fields.iteritems():
                    if len(field_tuple) >= 3:
                        column = field_tuple[2]
                        log += update_defaults(model_name, field_name, column)

        log += "\nReplacing %s taxes on accounts and products\n" % (
            self.env.context['type_tax_use'])
        for (model, field) in [
            # make this a configurable list of ir_model_fields one day?
                ('account.account', 'tax_ids'),
                ('product.product', 'supplier_taxes_id'),
                ('product.product', 'taxes_id'),
                ('product.template', 'supplier_taxes_id'),
                ('product.template', 'taxes_id')]:
            curr_model = self.env[model]
            obj_ids = curr_model.with_context(local_context).search(
                [(field, 'in', tax_map.keys())])
            for obj in obj_ids.read([field]):
                new_val = []
                write = False
                for i in obj[field]:
                    if i in tax_map:
                        write = True
                    new_val.append(tax_map.get(i, i))
                if write:
                    curr_model.browse(obj['id']).write(
                        {field: [(6, 0, new_val)]})
                    log += "Value (%s => %s) for %s,%s,%s\n" % (
                        obj[field], new_val, model, field, obj['id'])
        self[0].write(
            {
                'log': log,
                '%s_set_defaults' % self.env.context['type_tax_use']: True
            })

        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_id': self[0].id,
            'nodestroy': True,
        }

    @api.multi
    def set_inactive(self):
        if not self.env.context or not self.env.context.get('type_tax_use'):
            raise ValidationError(_("Can not detect tax use type"))
        tax_lines = self['%s_line_ids' % self.env.context['type_tax_use']]
        tax_model = self.env['account.tax']
        tax_ids = tax_model.search(
            [('id', 'in', [x.source_tax_id.id for x in tax_lines])])
        tax_ids.write({'active': False})
        log = (self.log or '') + (
            "\n*** %s: Setting %s %s taxes inactive\n" % (
                fields.Datetime.now(),
                len(tax_ids),
                self.env.context['type_tax_use']))
        self.write(
            {'log': log,
             '%s_set_inactive' % self.env.context['type_tax_use']: True})
        return {
            'name': self._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'domain': [],
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
            'nodestroy': True,
        }


class UpdateTaxConfigLine(models.Model):
    _name = 'account.update.tax.config.line'
    _description = "Tax update configuration lines"
    _rec_name = 'source_tax_id'

    @api.depends('sale_config_id', 'purchase_config_id')
    def _get_config_field(self):
        for this in self:
            config = this.sale_config_id or this.purchase_config_id
            if config:
                this.state = config.state
            else:
                this.state = False

    purchase_config_id = fields.Many2one(
        'account.update.tax.config',
        'Configuration')
    sale_config_id = fields.Many2one(
        'account.update.tax.config',
        'Configuration')
    source_tax_id = fields.Many2one(
        'account.tax', 'Source tax',
        required=True)
    source_tax_description = fields.Char(
        related='source_tax_id.description',
        string="Old tax description")
    target_tax_id = fields.Many2one(
        'account.tax', 'Target tax')
    target_tax_description = fields.Char(
        string="New tax description")
    amount_old = fields.Float(
        related='source_tax_id.amount',
        digits=(14, 4),
        string='Old amount', readonly=True)
    amount_new = fields.Float(
        digits=(14, 4),
        string='New amount')
    state = fields.Char(compute=_get_config_field)
