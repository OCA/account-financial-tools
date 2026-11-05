# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAssetLine(models.Model):
    _inherit = "account.asset.line"

    quantity = fields.Integer(readonly=True)
