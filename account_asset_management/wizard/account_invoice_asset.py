# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountInvoiceAsset(models.TransientModel):
    _name = 'account.invoice.asset'
    _description = 'Wizard to add invoice from invoice'

    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    move_id = fields.Many2one('account.move', 'Account move')
    move_line_ids = fields.Many2many('account.move.line', string='Account move line')
    reference = fields.Char('Reference', related='invoice_id.reference')
    partner_id = fields.Many2one('res.partner', 'Partner', related='invoice_id.partner_id')
    date_invoice = fields.Date('Date invoice', related='invoice_id.date_invoice')
    invoice_line_ids = fields.One2many('account.invoice.asset.lines', 'wizard_asset_id', string='Invoice lines')

    @api.multi
    def rebuild_account_move(self):
        for record in self:
            if record.move_id and len(record.invoice_line_ids.ids) > 0:
                inv_line_ids = record.invoice_line_ids.mapped('invoice_line_id').ids
                if len(inv_line_ids) > 0:
                    move = record.move_id
                    inv = record.invoice_id
                    for line in inv.invoice_line_ids.filtered(lambda r: r.id not in inv_line_ids and r.asset_profile_id):
                        line.write({
                                    'asset_profile_id': False,
                                    'tax_profile_id': False,
                                    })
                    for move_line in inv.move_id.line_ids:
                        if move_line.asset_id:
                            move_line.asset_id.unlink()
                    inv.move_id = False
                    move.button_cancel()
                    move.unlink()
                    inv.action_move_create()
            elif not record.move_id and len(record.invoice_line_ids.ids) > 0:
                inv = record.invoice_id
                inv_line_ids = record.invoice_line_ids.mapped('invoice_line_id').ids
                if len(inv_line_ids) > 0:
                    for line in inv.invoice_line_ids.filtered(lambda r: r.id not in inv_line_ids and r.asset_profile_id):
                        line.write({
                                    'asset_profile_id': False,
                                    'tax_profile_id': False,
                                    })
        return True


class AccountInvoiceAssetLines(models.TransientModel):
    _name = 'account.invoice.asset.lines'
    _description = 'Wizard to add invoice from invoice lines'

    wizard_asset_id = fields.Many2one('account.invoice.asset', 'Wizard account invoice asset', index=True,
                                      ondelete='cascade')
    invoice_line_id = fields.Many2one('account.invoice.line', 'Invoice line')
    product_id = fields.Many2one('product.product', 'Product', related='invoice_line_id.product_id')
    account_id = fields.Many2one('account.account', 'Account', related='invoice_line_id.account_id')
    asset_profile_id = fields.Many2one('account.asset.profile', 'Asset profile', related='invoice_line_id.asset_profile_id')
    tax_asset_profile_id = fields.Many2one('account.bg.asset.profile', 'Tax asset profile', related="invoice_line_id.tax_profile_id")
    quantity = fields.Float('Quantity', related='invoice_line_id.quantity', store=True)
    uom_id = fields.Many2one('product.uom', 'UOM', related='invoice_line_id.uom_id')
    price_unit = fields.Float('Unit price', related='invoice_line_id.price_unit')
    price_subtotal = fields.Monetary('Total', related='invoice_line_id.price_subtotal')
    price_total = fields.Monetary('Total', related='invoice_line_id.price_total')
    currency_id = fields.Many2one('res.currency', 'Currency', related='invoice_line_id.currency_id')
