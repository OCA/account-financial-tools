# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import math


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    equipment_ids = fields.Many2many(
        comodel_name="maintenance.equipment", compute="_compute_equipment_ids",
        string="Equipments",
    )

    @api.multi
    @api.depends('invoice_line_ids', 'invoice_line_ids.equipment_ids')
    def _compute_equipment_ids(self):
        for invoice in self:
            invoice.equipment_ids = [
                (6, 0, invoice.mapped('invoice_line_ids.equipment_ids').ids),
            ]

    @api.multi
    def action_invoice_cancel(self):
        res = super(AccountInvoice, self).action_invoice_cancel()
        self.mapped('equipment_ids').unlink()
        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    equipment_ids = fields.One2many(
        comodel_name="maintenance.equipment", inverse_name="invoice_line_id",
        string="Equipments",
    )

    def _prepare_equipment_vals_list(self, invoice_line):
        vals_list = []
        num = int(math.ceil(invoice_line.quantity))
        for i in range(num):
            vals_list.append({
                'name': "{} [{}/{}]".format(invoice_line.name, i + 1, num),
                'category_id': (
                    invoice_line.asset_category_id.equipment_category_id.id
                ),
                'invoice_line_id': invoice_line.id,
                'cost': invoice_line.price_subtotal / invoice_line.quantity,
                'partner_id': invoice_line.invoice_id.partner_id.id,
            })
        return vals_list

    @api.multi
    def asset_create(self):
        for line in self.filtered('asset_category_id.equipment_category_id'):
            # Create equipments
            equipments = self.env['maintenance.equipment']
            for vals in self._prepare_equipment_vals_list(line):
                equipments += equipments.create(vals)
            # Link assets to equipments
            # HACK: There's no way to inherit method knowing the created asset
            prev_assets = self.env['account.asset.asset'].search([])
            super(AccountInvoiceLine, line).asset_create()
            current_assets = self.env['account.asset.asset'].search([])
            asset = current_assets - prev_assets
            asset.write({'equipment_ids': [(4, x) for x in equipments.ids]})
