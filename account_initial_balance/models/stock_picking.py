# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    is_initial_balance = fields.Boolean('This is initial balance')
