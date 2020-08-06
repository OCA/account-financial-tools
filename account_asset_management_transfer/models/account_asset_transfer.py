# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class AccountAssetTransfer(models.Model):
    _name = "account.asset.transfer"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Asset Transfer"
    _order = "name desc"

    name = fields.Char(
        string="Asset Name",
        required=True,
        readonly=True,
        default="/",
        copy=False,
        tracking=True,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        default=lambda self: self._default_journal_id(),
        required=True,
        tracking=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Prepared By",
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    date_transfer = fields.Date(
        required=True, default=lambda self: fields.Date.context_today(self),
    )
    move_id = fields.Many2one(
        comodel_name="account.move", string="Journal Entries", readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("done", "Transferred"),
            ("cancel", "Cancelled"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self._default_company_id(),
    )
    company_currency_id = fields.Many2one(
        comodel_name="res.currency",
        related="company_id.currency_id",
        readonly=True,
        store=True,
    )
    source_asset_value = fields.Monetary(
        compute="_compute_asset_value", currency_field="company_currency_id",
    )
    source_asset_count = fields.Integer(compute="_compute_asset_count",)
    source_asset_ids = fields.Many2many(
        comodel_name="account.asset",
        # domain=[("state", "in", ("open", "close"))],
    )
    target_asset_value = fields.Monetary(
        compute="_compute_asset_value", currency_field="company_currency_id",
    )
    target_asset_count = fields.Integer(compute="_compute_asset_count",)
    target_asset_ids = fields.One2many(
        comodel_name="account.asset.transfer.target", inverse_name="transfer_id",
    )
    new_asset_ids = fields.Many2many(
        comodel_name="account.asset",
        relation="asset_transfer_asset_rel",
        column1="transfer_id",
        column2="asset_id",
        string="New Assets",
        readonly=True,
    )

    def _default_journal_id(self):
        asset_transfer_settings = self.env.user.company_id.asset_transfer_settings
        journal_id = False
        if asset_transfer_settings:
            journal_id = self.env.user.company_id.asset_transfer_journal_id.id
        return journal_id

    def _compute_asset_count(self):
        for rec in self:
            rec.source_asset_count = len(rec.source_asset_ids)
            rec.target_asset_count = len(rec.new_asset_ids)

    @api.depends("source_asset_ids", "target_asset_ids")
    def _compute_asset_value(self):
        for rec in self:
            rec.source_asset_value = sum(rec.source_asset_ids.mapped("purchase_value"))
            rec.target_asset_value = sum(
                rec.target_asset_ids.mapped("depreciation_base")
            )

    @api.model
    def _default_company_id(self):
        return self.env.company

    def open_entries(self):
        self.ensure_one()
        context = dict(self.env.context)
        context.pop("group_by", None)
        return {
            "name": _("Journal Entries"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": context,
            "domain": [("id", "in", self.move_id.ids)],
        }

    def open_source_asset(self):
        self.ensure_one()
        action = self.env.ref("account_asset_management.account_asset_action")
        result = action.read()[0]
        dom = [("id", "in", self.source_asset_ids.ids)]
        result.update({"domain": dom})
        return result

    def open_target_asset(self):
        self.ensure_one()
        action = self.env.ref("account_asset_management.account_asset_action")
        result = action.read()[0]
        dom = [("id", "in", self.new_asset_ids.ids)]
        result.update({"domain": dom})
        return result

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"]
                .with_context(ir_sequence_date=vals.get("date_transfer"))
                .next_by_code("account.asset.transfer")
            )
        return super().create(vals)

    def _prepare_move_dict(self, journal_id, line_ids, date, ref):
        move_dict = {
            "journal_id": journal_id,
            "line_ids": line_ids,
            "date": date,
            "ref": ref,
        }
        return move_dict

    def _prepare_move_line_dict(
        self,
        account_id,
        partner_id,
        name,
        credit=0.0,
        debit=0.0,
        asset_id=False,
        asset_profile=False,
    ):
        move_lines = {
            "asset_id": asset_id,
            "account_id": account_id,
            "partner_id": partner_id,
            "name": name,
            "credit": credit,
            "debit": debit,
            "asset_profile_id": asset_profile,
        }
        return move_lines

    def _check_configured_asset(self):
        if (
            float_compare(
                sum(self.mapped("source_asset_value")),
                sum(self.mapped("target_asset_value")),
                precision_rounding=2,
            )
            != 0
        ):
            raise ValidationError(_("Source and Target value must equal."))
        min_value_asset = self.mapped("source_asset_ids").mapped(
            "profile_id.account_min_value_id"
        )
        plus_value_asset = self.mapped("source_asset_ids").mapped(
            "profile_id.account_plus_value_id"
        )
        if not (plus_value_asset and min_value_asset):
            raise ValidationError(
                _(
                    "Source Asset(s) is not configured 'Plus-Value Account'"
                    " or 'Min-Value Account' in Asset Profile."
                )
            )
        return True

    def transfer(self):
        """
        The Concept
            * A new asset will be created
            * All source asset will be removed
            * Support transfering the asset with depre.
        Example :
            Buy Mobile 10000.0 THB. and run depreciation 1 times.
            Next, We need split to Battery 1000.0 THB. and Case 9000.0 THB.
        Account Moves :
            Dr Accumulated depreciation of transfer assets (for each asset, if any)
                Cr Asset Value of trasferring assets (for each asset)
            Dr Asset Value to the new asset
                Cr Accumulated Depreciation of to the new asset (if any)
        =====================================================
        | Description                   |   Debit |   Credit|
        =====================================================
        | Vendor Bills                  |         | 10000.0 |
        | Mobile                        | 10000.0 |         |
        -------Run Depreciation 1 times----------------------
        | Accumulated Depre.            |         |    50.0 |
        | Depre. Expense                |    50.0 |         |
        -------Run Depreciation before remove----------------
        | Accumulated Depre.            |         |   150.0 |
        | Depre. Expense                |   150.0 |         |
        -------Remove Asset----------------------------------
        | Mobile                        |         | 10000.0 |
        | Accumulated Depre.            |   200.0 |         |
        | Loss Account                  |  9800.0 |         |
        -------New Asset-------------------------------------
        | Battery                       |  1000.0 |         |
        | Battery (Ratio Depreciation)  |         |    20.0 |
        | Case                          |  9000.0 |         |
        | Case (Ratio Depreciation)     |         |   180.0 |
        """
        self._check_configured_asset()
        AccountMove = self.env["account.move"]
        AssetRemove = self.env["account.asset.remove"]
        for rec in self:
            move_lines = []
            new_assets_ids = []
            accum_depre = 0.0
            total_depre = sum(rec.source_asset_ids.mapped("value_depreciated"))
            # Step 1 : Source Asset Management
            # - Prepared move line for reconciled with
            # asset and depreciated value (if any).
            # - Removed source asset
            for asset in rec.source_asset_ids:
                if asset.purchase_value:
                    account_aml_asset = asset.account_move_line_ids.filtered(
                        lambda l: l.asset_profile_id
                    ).account_id.id
                    if not account_aml_asset:
                        raise ValidationError(
                            _("'%s' don't have move line" % asset.name)
                        )
                    cr_move_line_dict = rec._prepare_move_line_dict(
                        account_aml_asset,
                        asset.partner_id.id,
                        asset.display_name,
                        credit=asset.purchase_value,
                        debit=0.0,
                    )
                    move_lines.append((0, 0, cr_move_line_dict))
                if asset.value_depreciated:
                    move_line_dict = rec._prepare_move_line_dict(
                        asset.profile_id.account_depreciation_id.id,
                        asset.partner_id.id,
                        asset.display_name,
                        credit=0.0,
                        debit=asset.value_depreciated,
                    )
                    move_lines.append((0, 0, move_line_dict))
                account_plus_value_id = asset.profile_id.account_plus_value_id
                account_min_value_id = asset.profile_id.account_min_value_id
                remove_wizard = AssetRemove.create(
                    {
                        "date_remove": rec.date_transfer,
                        "account_plus_value_id": account_plus_value_id.id,
                        "account_min_value_id": account_min_value_id.id,
                    }
                )
                remove_wizard.with_context(
                    {"active_id": asset.id, "early_removal": True}
                ).remove()
            # Step 2 : Target Asset Management
            # - Prepared new asset move line and depreciation move line (if any).
            # - Create Move and auto post for create new asset
            for target_asset in rec.target_asset_ids:
                asset_profile = target_asset.asset_profile_id
                if target_asset.depreciation_base:
                    new_asset_move_line_dict = rec._prepare_move_line_dict(
                        asset_profile.account_asset_id.id,
                        rec.source_asset_ids[0].partner_id.id,
                        target_asset.asset_name,
                        credit=0.0,
                        debit=target_asset.depreciation_base,
                        asset_profile=asset_profile.id,
                    )
                    move_lines.append((0, 0, new_asset_move_line_dict))
                # Depreciation Move Line
                if total_depre:
                    ratio = 1.0
                    if rec.source_asset_value:
                        ratio = target_asset.depreciation_base / rec.source_asset_value
                    if target_asset.id == rec.target_asset_ids[-1].id:
                        new_depre = total_depre - accum_depre
                    else:
                        new_depre = ratio * total_depre
                    new_depre_dict = rec._prepare_move_line_dict(
                        asset_profile.account_asset_id.id,
                        rec.source_asset_ids[0].partner_id.id,
                        target_asset.asset_name,
                        credit=new_depre,
                        debit=0.0,
                    )
                    move_lines.append((0, 0, new_depre_dict))
                    accum_depre += new_depre
            move_dict = rec._prepare_move_dict(
                rec.journal_id.id, move_lines, rec.date_transfer, rec.name
            )
            move = AccountMove.create(move_dict)
            move.with_context({"asset_transfer": rec.name}).action_post()
            # Step 3 : Update value in new asset,
            # if source asset have a depreciated value.
            for target_asset in rec.target_asset_ids:
                depre_ml = move.line_ids.filtered(
                    lambda l: l.account_id.id
                    == target_asset.asset_profile_id.account_asset_id.id
                    and l.name == target_asset.asset_name
                )
                new_asset_id = depre_ml.asset_id
                purchase_value_with_depre = new_asset_id.purchase_value - sum(
                    depre_ml.mapped("credit")
                )
                if (
                    float_compare(
                        purchase_value_with_depre,
                        new_asset_id.purchase_value,
                        precision_digits=2,
                    )
                    != 0.0
                ):
                    new_asset_id.write({"purchase_value": purchase_value_with_depre})
                    new_asset_id.with_context(
                        {"allow_asset_line_update": True}
                    )._onchange_purchase_salvage_value()
                new_assets_ids.append((4, new_asset_id.id))
            rec.write(
                {"new_asset_ids": new_assets_ids, "move_id": move.id, "state": "done"}
            )
        return True

    def set_to_draft(self):
        return self.write({"state": "draft"})

    def cancel(self):
        return self.write({"state": "cancel"})


class AccountAssetTransferTarget(models.Model):
    _name = "account.asset.transfer.target"
    _description = "Asset Transfer Target"

    transfer_id = fields.Many2one(comodel_name="account.asset.transfer",)
    asset_profile_id = fields.Many2one(
        comodel_name="account.asset.profile", string="To Asset Category", required=True,
    )
    asset_name = fields.Char(required=True)
    depreciation_base = fields.Float(string="Value", required=True, default=0.0,)
