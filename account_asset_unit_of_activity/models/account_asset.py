# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AccountAsset(models.Model):
    _inherit = "account.asset"

    total_number_of_use = fields.Integer(
        compute="_compute_total_number_of_use",
        readonly=False,
        store=True,
    )
    remaining_usage = fields.Integer(compute="_compute_remaining_usage")
    has_depreciation_accounting_entry = fields.Boolean(
        compute="_compute_has_depreciation_accounting_entry"
    )

    @api.constrains("total_number_of_use", "method")
    def _check_number_of_use(self):
        for asset in self:
            if asset.method != "unit-activity":
                continue
            if asset.total_number_of_use == 0:
                raise ValidationError(self.env._("Number of usage can't be null."))
            if asset.total_number_of_use < 0:
                raise ValidationError(self.env._("Number of usage can't be negative."))

    @api.depends("total_number_of_use", "depreciation_line_ids.quantity")
    def _compute_remaining_usage(self):
        for asset in self:
            asset.remaining_usage = asset.total_number_of_use - sum(
                asset.depreciation_line_ids.filtered(
                    lambda line: line.type == "depreciate"
                ).mapped("quantity")
            )

    @api.depends("depreciation_line_ids.move_id", "depreciation_line_ids.type")
    def _compute_has_depreciation_accounting_entry(self):
        for asset in self:
            asset.has_depreciation_accounting_entry = bool(
                asset.depreciation_line_ids.filtered(
                    lambda line: line.type == "depreciate"
                )
            )

    @api.depends("profile_id")
    def _compute_total_number_of_use(self):
        for asset in self:
            asset.total_number_of_use = asset.profile_id.total_number_of_use

    def add_unit_of_activity(self):
        self.ensure_one()
        return {
            "name": self.env._("Add Asset Unit of activity"),
            "type": "ir.actions.act_window",
            "res_model": "account.asset.unit.of.activity",
            "view_mode": "form",
            "target": "new",
            "context": dict(self.env.context, active_ids=self.ids, active_id=self.id),
        }

    def compute_depreciation_board(self):
        # The depreciation board of a 'unit-activity' asset is not computed
        # automatically: the depreciation lines are added manually through
        # the 'Add Unit of Activity' wizard.
        other_assets = self.filtered(lambda asset: asset.method != "unit-activity")
        return super(AccountAsset, other_assets).compute_depreciation_board()
