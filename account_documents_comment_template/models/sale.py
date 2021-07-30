# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    static_template_id = fields.Many2one('base.comment.template', 'Comment Template', related="product_prop_static_id.comment_template_id",
                                          domain="[('position', '=', 'prints')]")
    static_note = fields.Html(string='Comment summary', related="product_prop_static_id.comment_template_id.text", store=True)
