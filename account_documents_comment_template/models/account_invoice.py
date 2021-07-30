# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    static_template_id = fields.Many2one('base.comment.template', 'Comment Template', related="product_prop_static_id.comment_template_id",
                                          domain="[('position', '=', 'prints')]")
    static_note = fields.Html(string='Comment summary', related="product_prop_static_id.comment_template_id.text", store=True)

    @api.onchange('static_template_id')
    @api.depends('product_prop_static_id.comment_template_id', 'static_note')
    def _onchange_static_template_id(self):
        if self.static_template_id:
            self.static_note = self.product_prop_static_id.comment_template_id.text
