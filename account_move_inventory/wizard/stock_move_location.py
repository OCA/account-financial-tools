# Copyright (C) 2011 Julius Network Solutions SARL <contact@julius.fr>
# Copyright 2018 Camptocamp SA
# Copyright 2019 Sergio Teruel - Tecnativa <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models, _
from odoo.fields import first
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)


class StockMoveLocationWizard(models.TransientModel):
    _inherit = "wiz.stock.move.location"

    edit_accounts = fields.Boolean(string='Edit accounts')
    property_stock_account_input = fields.Many2one(
        'account.account', 'Stock Input Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )
    property_stock_account_output = fields.Many2one(
        'account.account', 'Stock Output Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )
    property_stock_valuation_account_id = fields.Many2one(
        'account.account', 'Stock Valuation Account',
        company_dependent=True, domain=[('deprecated', '=', False)],
        )
    company_id = fields.Many2one(
        'res.company', 'Company',
        required=True,
        default=lambda self: self.env['res.company']._company_default_get('stock.inventory'))

    @api.onchange('edit_accounts')
    def _onchage_edit_accounts(self):
        if not self.edit_accounts:
            self.property_stock_account_input = False
            self.property_stock_account_output = False
            self.property_stock_valuation_account_id = False

    def _create_inventory(self):
        return self.env['stock.inventory'].create({
            "name": _("INV: from %s to %s" % (self.property_stock_account_output.code, self.property_stock_account_input.code)),
            "location_id": self.origin_location_id.id,
            "filter": 'partial',
            "edit_accounts": self.edit_accounts,
            "property_stock_account_input": self.property_stock_account_input and self.property_stock_account_input.id or False,
            "property_stock_account_output": self.property_stock_account_output and self.property_stock_account_output.id or False,
            "property_stock_valuation_account_id": self.property_stock_valuation_account_id and self.property_stock_valuation_account_id.id or False,
        })

    @api.multi
    def _create_inventory_lines(self, inventory):
        self.ensure_one()
        inv_line = self.env['stock.inventory.line']
        for line in self.stock_move_location_line_ids:
            if line.destination_location_id != line.origin_location_id:
                inv_line |= self.env['stock.inventory.line'].create({
                    'inventory_id': inventory.id,
                    'partner_id': self.owner_id and self.owner_id.id or False,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'location_id': line.origin_location_id.id,
                    'package_id': line.package_id and line.package_id or False,
                    'prod_lot_id': line.lot_id and line.lot_id.id or False,
                    'product_qty': line.max_quantity - line.move_quantity,
                })
                inv_line |= self.env['stock.inventory.line'].create({
                    'inventory_id': inventory.id,
                    'partner_id': self.owner_id and self.owner_id.id or False,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.product_uom_id.id,
                    'location_id': line.destination_location_id.id,
                    'package_id': line.package_id and line.package_id or False,
                    'prod_lot_id': line.lot_id and line.lot_id.id or False,
                    'product_qty': line.move_quantity,
                })
            return inv_line

    @api.multi
    def action_move_location(self):
        for record in self:
            if record.edit_accounts:
                inventory = record._create_inventory()
                record._create_inventory_lines(inventory)
                if not self.env.context.get("planned"):
                    inventory.action_start()
                return record._get_inventory_action(inventory.id)
        return super(StockMoveLocationWizard, self).action_move_location()

    def _get_inventory_action(self, inventory_id):
        action = self.env.ref("stock.action_inventory_form").read()[0]
        form_view = self.env.ref("stock.view_inventory_form").id
        action.update({
            "view_mode": "form",
            "views": [(form_view, "form")],
            "res_id": inventory_id,
        })
        return action