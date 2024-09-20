# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAssetProfile(models.Model):
    _inherit = "account.asset.profile"

    use_sequence = fields.Boolean(
        string="Auto Asset Number by Sequence",
        default=False,
        help="If check, asset number auto run by sequence.",
    )
    sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Asset Number Sequence",
        domain=lambda self: self._get_domain_sequence_id(),
    )
    barcode_type = fields.Selection(
        selection=[("barcode", "Barcode"), ("qr", "QR")],
        default="barcode",
    )
    barcode_width = fields.Integer(
        default=350,
        help="Width (in px) of the barcode or the QR code",
    )
    barcode_height = fields.Integer(
        default=75,
        help="Height (in px) of the barcode or the QR code",
    )

    @api.model
    def _get_domain_sequence_id(self):
        return [("company_id", "in", [False, self.env.company.id])]

    @api.onchange("barcode_type")
    def _onchange_barcode_type(self):
        # Set default values when type is changed
        if self.barcode_type == "barcode":
            self.barcode_width = 300
            self.barcode_height = 75
        elif self.barcode_type == "qr":
            self.barcode_width = 150
