from odoo import _, api, exceptions, fields, models


class AccountAssetUnitOfActivity(models.TransientModel):
    _name = "account.asset.unit.of.activity"
    _description = "Compute Assets unit of activity"

    auto_create_asset_move = fields.Boolean(
        String="Create move automatically",
        help="If the other asset line has all a move created,\
             the move associated to this asset line will be created automatically",
    )
    quantity = fields.Integer(default=1)
    date = fields.Date(default=fields.date.today())

    @api.constrains("date")
    def _check_date(self):
        asset_id = self.env.context.get("active_id")
        asset = self.env["account.asset"].browse(asset_id)
        if asset.method == "unit-activity":
            if self.date < asset.date_start:
                raise exceptions.ValidationError(
                    _("Date can't be before assert start date")
                )
            dline = asset.depreciation_line_ids.filtered(
                lambda line: line.type == "depreciate"
            )
            if dline and self.date < dline.sorted("line_date")[-1].line_date:
                raise exceptions.UserError(
                    _(
                        "The date is before last asset line,\n"
                        "Please enter usages in chronologic order"
                    )
                )

    def add_usage(self):
        asset_id = self.env.context.get("active_id")
        asset = self.env["account.asset"].browse(asset_id)
        if self.quantity > asset.remaining_usage:
            raise exceptions.UserError(
                _("The number of remaining asset usage\n" "is exceed")
            )
        if asset.remaining_usage == 0:
            raise exceptions.UserError(
                _(
                    "The asset is totaly depreciated.\n"
                    "You can't add depreciation line"
                )
            )
        if self.quantity < 0:
            raise exceptions.UserError(_("The quantity can't be negative"))
        vals = self._compute_values(asset_id)
        vals.update(
            {
                "line_date": self.date,
                "type": "depreciate",
                "asset_id": asset_id,
                "init_entry": False,
                "quantity": self.quantity,
            }
        )
        aal = self.env["account.asset.line"].create(vals)
        if self.auto_create_asset_move:
            aal.create_move()

    def _compute_values(self, asset_id):
        asset = self.env["account.asset"].browse(asset_id)
        company = asset.company_id
        currency = company.currency_id
        step = (asset.purchase_value - asset.salvage_value) / asset.total_number_of_use
        dlines = asset.depreciation_line_ids.filtered(lambda r: r.type == "depreciate")
        amount = currency.round(self.quantity * step)
        if self.quantity == asset.remaining_usage:
            if dlines:
                amount = dlines[-1].remaining_value
            else:
                amount = asset.purchase_value
        return {
            "amount": amount,
            "previous_id": dlines[-1].id if dlines else None,
        }
