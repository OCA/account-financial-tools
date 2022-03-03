from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    revaluation_auto_created = fields.Boolean(string="Automated Inventory Revaluation")
