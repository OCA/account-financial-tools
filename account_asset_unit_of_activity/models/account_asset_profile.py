# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAssetProfile(models.Model):
    _inherit = "account.asset.profile"

    total_number_of_use = fields.Integer()

    @api.model
    def _selection_method(self):
        return super()._selection_method() + [
            ("unit-activity", self.env._("Unit of Activity")),
        ]
