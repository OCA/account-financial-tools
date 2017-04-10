# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'

    equipment_category_id = fields.Many2one(
        comodel_name="maintenance.equipment.category",
        string="Equipment category",
        help="This category will be used for the created equipment when it "
             "is created automatically on validating a vendor bill that "
             "contains this asset category.",
    )
