# -*- coding: utf-8 -*-
from openerp import api, models, fields


class SelectTaxes(models.TransientModel):
    _name = 'account.update.tax.select_taxes'
    _description = 'Select the taxes to be updated'

    type_tax_use = fields.Char('Type tax use', readonly=True)
    config_id = fields.Many2one(
        'account.update.tax.config',
        'Configuration', readonly=True)
    tax_ids = fields.Many2many(
        'account.tax', string='Taxes')
    covered_tax_ids = fields.Many2many(
        'account.tax', string='Covered taxes')

    @api.multi
    def save_taxes(self):
        """
        Create tax lines in the update tax configuration
        based on a user selection of taxes.
        From these taxes, gather their hierarchically related
        other taxes which need to be duplicated to.
        From this gathering, ignore any taxes that might
        have been added by the user earlier on.
        """
        line_model = self.env['account.update.tax.config.line']

        def add_tree(tax):
            result = [tax]
            for child in tax.children_tax_ids:
                result += add_tree(child)
            return result

        covered = [x.source_tax_id.id for x in
                   (self.config_id.sale_line_ids +
                    self.config_id.purchase_line_ids)]
        taxes = []
        # add all the children
        # removed the parent_id search in v9 not being there a single parent.
        for tax in self.tax_ids:
            taxes += add_tree(tax)
        for tax in filter(lambda x: x.id not in covered, taxes):
            line_model.create(
                {'%s_config_id' % self.type_tax_use: self.config_id.id,
                 'source_tax_id': tax.id, },)
        return {'type': 'ir.actions.act_window_close'}
