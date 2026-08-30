# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCurrency(models.Model):
    _inherit = "res.currency"

    cash_unit_ids = fields.One2many("cash.unit", "currency_id", string="Cash Units")
