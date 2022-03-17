# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    landed_cost_id = fields.Many2one('stock.landed.cost', 'Landed cost')
