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

    @api.model
    def _get_domain_sequence_id(self):
        return [("company_id", "in", [False, self.env.company.id])]
