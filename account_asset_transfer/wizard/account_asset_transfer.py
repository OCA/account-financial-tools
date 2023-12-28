# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountAssetTransfer(models.TransientModel):
    _name = "account.asset.transfer"
    _inherit = "analytic.mixin"
    _description = "Transfer Asset"
    _check_company_auto = True

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
    )
    transfer_journal_id = fields.Many2one(
        comodel_name="account.journal",
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        string="Transfer Journal",
        required=True,
        check_company=True,
    )
    date_transfer = fields.Date(
        string="Transfer Date",
        required=True,
        default=fields.Date.today,
        help="Transfer date must be after the asset journal entry",
    )
    note = fields.Text("Notes")
    from_asset_ids = fields.Many2many(
        comodel_name="account.asset",
        string="From Asset(s)",
        readonly=True,
    )
    to_asset_ids = fields.One2many(
        comodel_name="account.asset.transfer.line",
        inverse_name="transfer_id",
        string="To Asset(s)",
    )
    from_asset_value = fields.Monetary(
        string="From Value",
        compute="_compute_asset_value",
    )
    to_asset_value = fields.Monetary(
        string="To Value",
        compute="_compute_asset_value",
    )
    balance = fields.Monetary(
        compute="_compute_asset_value",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        from_asset_ids = self.env.context.get("active_ids")
        assets = self.env["account.asset"].browse(from_asset_ids)
        # Prepare default values
        company = assets.mapped("company_id")
        company.ensure_one()
        journals = assets.mapped("profile_id.transfer_journal_id")
        partners = assets.mapped("partner_id")
        analytics = assets.mapped("analytic_distribution")
        # Combine analytic to dict
        analytic_dict = {}
        unique_elements = set()
        for analytic in analytics:
            if analytic is not False:
                for key, value in analytic.items():
                    if key not in analytic_dict and key not in unique_elements:
                        analytic_dict[key] = value
                        unique_elements.add(key)
        # Assign values
        res["company_id"] = company.id
        res["partner_id"] = partners[0].id if len(partners) == 1 else False
        res["from_asset_ids"] = [(4, asset_id) for asset_id in assets.ids]
        res["transfer_journal_id"] = journals[:1].id
        res["analytic_distribution"] = analytic_dict
        return res

    @api.depends("from_asset_ids", "to_asset_ids")
    def _compute_asset_value(self):
        for rec in self:
            rec.from_asset_value = sum(rec.from_asset_ids.mapped("purchase_value"))
            rec.to_asset_value = sum(rec.to_asset_ids.mapped("asset_value"))
            balance = rec.from_asset_value - rec.to_asset_value
            rec.balance = balance if balance > 0 else 0

    def _check_amount_transfer(self):
        self.ensure_one()
        if float_compare(self.from_asset_value, self.to_asset_value, 2) != 0:
            raise UserError(_("Total values of new assets must equal to source assets"))
        if self.to_asset_ids.filtered(lambda l: l.asset_value <= 0):
            raise UserError(_("Value of new asset must greater than 0.0"))

    def _get_new_move_transfer(self):
        return {
            "date": self.date_transfer,
            "journal_id": self.transfer_journal_id.id,
            "narration": self.note,
        }

    def transfer(self):
        self.ensure_one()
        self.from_asset_ids._check_can_transfer()
        self._check_amount_transfer()
        # Create transfer journal entry
        move_vals = self._get_new_move_transfer()
        move = self.env["account.move"].create(move_vals)
        move_lines = self._get_transfer_data()
        move.with_context(allow_asset=True).write({"line_ids": move_lines})
        # Post move and create new assets
        move.action_post()
        # Set source assets as removed
        self.from_asset_ids.write(
            {"state": "removed", "date_remove": self.date_transfer}
        )
        # Set all assets is transfer document
        move.line_ids.mapped("asset_id").write({"is_transfer": True})
        return {
            "name": _("Asset Transfer Journal Entry"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": self.env.context,
            "domain": [("id", "=", move.id)],
        }

    def _get_move_line_from_asset(self, asset):
        # Case asset created with account move
        if asset.account_move_line_ids:
            asset.account_move_line_ids.ensure_one()
            move_line = asset.account_move_line_ids[0]
            return {
                "name": move_line.name,
                "account_id": move_line.account_id.id,
                "analytic_distribution": move_line.analytic_distribution or {},
                "debit": move_line.credit,
                "credit": move_line.debit,
                "partner_id": move_line.partner_id.id,
                "asset_id": move_line.asset_id.id,  # Link to existing asset
            }
        # Case asset created without account moves
        else:
            return {
                "name": asset.name,
                "account_id": asset.profile_id.account_asset_id.id,
                "analytic_distribution": asset.analytic_distribution or {},
                "debit": 0.0,
                "credit": asset.purchase_value or 0.0,
                "partner_id": asset.partner_id.id,
                "asset_id": asset.id,  # Link to existing asset
            }

    def _get_move_line_to_asset(self, to_asset):
        return {
            "name": to_asset.asset_name,
            "account_id": to_asset.asset_profile_id.account_asset_id.id,
            "analytic_distribution": to_asset.analytic_distribution or {},
            "debit": to_asset.asset_value,
            "credit": 0.0,
            "partner_id": to_asset.partner_id.id,
            "asset_profile_id": to_asset.asset_profile_id.id,  # To create new asset
            "price_subtotal": to_asset.asset_value,
        }

    def _get_transfer_data(self):
        # Create lines from assets
        move_lines = [
            Command.create(self._get_move_line_from_asset(from_asset))
            for from_asset in self.from_asset_ids
        ]
        # Create lines for new assets
        move_lines += [
            Command.create(self._get_move_line_to_asset(to_asset))
            for to_asset in self.to_asset_ids
        ]
        return move_lines

    def expand_to_asset_ids(self):
        self.ensure_one()
        lines = self.to_asset_ids.filtered(lambda l: l.asset_profile_id and l.quantity)
        for line in lines:
            line._expand_asset_line()
        action = self.env.ref("account_asset_transfer.action_account_asset_transfer")
        result = action.sudo().read()[0]
        result.update({"res_id": self.id})
        return result


class AccountAssetTransferLine(models.TransientModel):
    _name = "account.asset.transfer.line"
    _inherit = "analytic.mixin"
    _description = "Transfer To Asset"

    transfer_id = fields.Many2one(
        comodel_name="account.asset.transfer",
        index=True,
    )
    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset Profile",
        required=True,
    )
    asset_name = fields.Char(required=True)
    quantity = fields.Float(
        required=True,
        default=0.0,
    )
    price_unit = fields.Float(
        string="Unit Price",
        required=True,
        default=0.0,
    )
    asset_value = fields.Float(
        compute="_compute_asset_value",
        default=0.0,
        store=True,
        required=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )

    @api.depends("quantity", "price_unit")
    def _compute_asset_value(self):
        for rec in self:
            rec.asset_value = rec.quantity * rec.price_unit

    def _expand_asset_line(self):
        self.ensure_one()
        profile = self.asset_profile_id
        if profile and self.quantity > 1.0 and profile.asset_product_item:
            line = self
            qty = self.quantity
            name = self.asset_name
            self.update({"quantity": 1, "asset_name": "{} {}".format(name, 1)})
            for i in range(1, int(qty)):
                line.copy({"asset_name": "{} {}".format(name, i + 1)})
