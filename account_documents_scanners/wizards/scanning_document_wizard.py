# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import models, api, fields, _


_logger = logging.getLogger(__name__)


class ScanningDocumentWizard(models.TransientModel):
    _name = 'scanning.document.wizard'
    _description = 'Scanning Document Wizard'

    scanning_scanner_id = fields.Many2one(comodel_name='scanners.scanner', string='Default Scanner',
                                          default=lambda self: self.env.user.scanning_scanner_id.id)

    scanner_depth = fields.Selection([
        ('50', '50 dpi'),
        ('100', '100 dpi'),
        ('150', '150 dpi'),
        ('200', '200 dpi'),
        ('300', '300 dpi'),
        ('400', '400 dpi'),
        ('600', '600 dpi'),
        ('1200', '1200 dpi')
        ], string='Resolution', default=lambda self: self.env.user.scanner_depth)

    scanner_color_mode = fields.Selection([
        ('Color', 'Color'),
        ('Monochrome', 'Monochrome'),
        ('Grayscale', 'Grayscale'),
        ], string='Mode', default=lambda self: self.env.user.scanner_color_mode)

    scanner_source_mode = fields.Selection([
        ('ADF', 'ADF'),
        ('Document Table', 'Document Table'),
        ], string='Document Source', default=lambda self: self.env.user.scanner_source_mode)

    @api.multi
    def action_ok(self):
        active_id = self._context.get('active_id')
        if not active_id:
            return
        res = self.env['account.documents'].browse(active_id)
        if res:
            for record in self:
                self.env['scanners.action'].scan_image(res,
                                                       scanner_depth=record.scanner_depth,
                                                       scanner_color_mode=record.scanner_color_mode,
                                                       scanner_source_mode=record.scanner_source_mode)
        return {'type': 'ir.actions.act_window_close'}
