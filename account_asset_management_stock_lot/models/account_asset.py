# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, exceptions, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    product_id = fields.Many2one(
        "product.product",
        string="Product",
        compute="_compute_product_id",
        store=True,
    )
    stock_lot_id = fields.Many2one("stock.lot", string="Lot/Serial Number")

    @api.depends("stock_lot_id")
    def _compute_product_id(self):
        for asset in self:
            if asset.stock_lot_id:
                asset.product_id = asset.stock_lot_id.product_id.id

    @api.constrains("stock_lot_id")
    def _check_unique_asset(self):
        for asset in self:
            lot = asset.stock_lot_id
            if lot.product_id.tracking == "serial" and len(lot.asset_ids) > 1:
                raise exceptions.UserError(
                    _("A serial number can't be linked to multiple assets")
                )
