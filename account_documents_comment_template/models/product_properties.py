# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _

import logging
_logger = logging.getLogger(__name__)


class ProductPropertiesStatic(models.Model):
    _inherit = "product.properties.static"

    comment_template_id = fields.Many2one('base.comment.template', 'Comment Template',
                                          domain="[('position', '=', 'prints')]")

    def _set_static_ignore_print_properties(self):
        res = super(ProductPropertiesStatic, self)._set_static_ignore_print_properties()
        return res+['comment_template_id']
