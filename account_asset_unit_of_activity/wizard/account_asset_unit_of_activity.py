# Copyright 2026 Akretion (https://www.akretion.com).
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountAssetUnitOfActivity(models.TransientModel):
    _name = "account.asset.unit.of.activity"
    _description = "Add a unit of activity on an asset"

    auto_create_asset_move = fields.Boolean(
        string="Create move automatically",
        help="If the other asset lines all have a move created, the move "
        "associated to this asset line will be created automatically.",
    )
    quantity = fields.Integer(default=1)
    date = fields.Date(default=fields.Date.context_today)

    @api.constrains("date")
    def _check_date(self):
        self.ensure_one()
        if not self.date:
            return
        asset = self._get_asset()
        if asset.method != "unit-activity":
            return
        if asset.date_start and self.date < asset.date_start:
            raise ValidationError(
                self.env._("The date can't be before the asset start date.")
            )
        depreciation_lines = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        )
        if (
            depreciation_lines
            and self.date < depreciation_lines.sorted("line_date")[-1].line_date
        ):
            raise UserError(
                self.env._(
                    "The date is before the last asset line.\n"
                    "Please enter usages in chronological order."
                )
            )

    def _get_asset(self):
        self.ensure_one()
        return self.env["account.asset"].browse(self.env.context.get("active_id"))

    def _prepare_asset_line_vals(self, asset):
        """Prepare the values of the depreciation line for the usage.

        The amount is the residual value for the last usage, so that the
        asset is fully depreciated at the end despite the rounding.
        """
        self.ensure_one()
        currency = asset.company_id.currency_id
        depreciation_lines = asset.depreciation_line_ids.filtered(
            lambda line: line.type == "depreciate"
        ).sorted("line_date")
        if self.quantity == asset.remaining_usage:
            amount = (
                depreciation_lines[-1].remaining_value
                if depreciation_lines
                else asset.depreciation_base
            )
        else:
            step = asset.depreciation_base / asset.total_number_of_use
            amount = currency.round(self.quantity * step)
        return {
            "asset_id": asset.id,
            "line_date": self.date,
            "type": "depreciate",
            "init_entry": False,
            "quantity": self.quantity,
            "amount": amount,
            "previous_id": depreciation_lines[-1].id if depreciation_lines else False,
        }

    def add_usage(self):
        self.ensure_one()
        asset = self._get_asset()
        if self.quantity < 0:
            raise UserError(self.env._("The quantity can't be negative."))
        if not asset.remaining_usage:
            raise UserError(
                self.env._(
                    "The asset is fully depreciated.\n"
                    "You can't add a depreciation line."
                )
            )
        if self.quantity > asset.remaining_usage:
            raise UserError(
                self.env._("The number of remaining asset usages is exceeded.")
            )
        line = self.env["account.asset.line"].create(
            self._prepare_asset_line_vals(asset)
        )
        if self.auto_create_asset_move:
            line.create_move()
        return {"type": "ir.actions.act_window_close"}
