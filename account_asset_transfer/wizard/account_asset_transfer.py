# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class AccountAssetTransfer(models.TransientModel):
    _name = "account.asset.transfer"
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
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic account",
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic tags",
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
        analytics = assets.mapped("account_analytic_id")
        tags = assets[:1].analytic_tag_ids
        for asset in assets:
            if asset.analytic_tag_ids != tags:
                # When not all tags are the same, no default
                tags = self.env["account.analytic.tag"]
                break
        # Assign values
        res["company_id"] = company.id
        res["partner_id"] = partners[0].id if len(partners) == 1 else False
        res["from_asset_ids"] = [(4, asset_id) for asset_id in assets.ids]
        res["transfer_journal_id"] = journals[:1].id
        res["analytic_account_id"] = analytics[0].id if len(analytics) == 1 else False
        res["analytic_tag_ids"] = [(4, tag_id) for tag_id in tags.ids]
        return res

    @api.depends("from_asset_ids", "to_asset_ids")
    def _compute_asset_value(self):
        for rec in self:
            rec.from_asset_value = sum(rec.from_asset_ids.mapped("purchase_value"))
            rec.to_asset_value = sum(rec.to_asset_ids.mapped("asset_value"))
            balance = rec.from_asset_value - rec.to_asset_value
            rec.balance = balance if balance > 0 else 0

    def _check_amount_trasnfer(self):
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
        self._check_amount_trasnfer()
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
        return {
            "name": _("Asset Transfer Journal Entry"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": self.env.context,
            "domain": [("id", "=", move.id)],
        }

    def _get_move_line_from_asset(self, move_line):
        return {
            "name": move_line.name,
            "account_id": move_line.account_id.id,
            "analytic_account_id": move_line.analytic_account_id.id,
            "analytic_tag_ids": [(4, tag.id) for tag in move_line.analytic_tag_ids],
            "debit": move_line.credit,
            "credit": move_line.debit,
            "partner_id": move_line.partner_id.id,
            "asset_id": move_line.asset_id.id,  # Link to existing asset
        }

    def _get_move_line_to_asset(self, to_asset):
        return {
            "name": to_asset.asset_name,
            "account_id": to_asset.asset_profile_id.account_asset_id.id,
            "analytic_account_id": to_asset.analytic_account_id.id,
            "analytic_tag_ids": [(4, tag.id) for tag in to_asset.analytic_tag_ids],
            "debit": to_asset.asset_value,
            "credit": 0.0,
            "partner_id": to_asset.partner_id.id,
            "asset_profile_id": to_asset.asset_profile_id.id,  # To create new asset
            "price_subtotal": to_asset.asset_value,
        }

    def _get_transfer_data(self):
        move_lines = []
        # Create lines from assets
        for asset in self.from_asset_ids:
            asset.account_move_line_ids.ensure_one()
            move_line = asset.account_move_line_ids[0]
            move_line_vals = self._get_move_line_from_asset(move_line)
            move_lines.append((0, 0, move_line_vals))
        # Create lines for new assets
        move_lines += [
            (0, 0, self._get_move_line_to_asset(to_asset))
            for to_asset in self.to_asset_ids
        ]
        return move_lines


class AccountAssetTransferLine(models.TransientModel):
    _name = "account.asset.transfer.line"
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
    asset_value = fields.Float(
        string="Asset Value",
        required=True,
        default=0.0,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic account",
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic tags",
    )
