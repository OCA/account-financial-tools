# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockLot(models.Model):
    _inherit = "stock.lot"

    asset_ids = fields.One2many("account.asset", "stock_lot_id", readonly=True)
