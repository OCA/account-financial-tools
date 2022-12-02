# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAssetLine(models.Model):
    _name = "account.asset.line"
    _description = "Asset depreciation table line"
    _order = "type, line_date"
    _check_company_auto = True

    name = fields.Char(string="Depreciation Name", size=64, readonly=True)
    asset_id = fields.Many2one(
        comodel_name="account.asset",
        string="Asset",
        required=True,
        ondelete="cascade",
        check_company=True,
        index=True,
    )
    previous_id = fields.Many2one(
        comodel_name="account.asset.line",
        string="Previous Depreciation Line",
        readonly=True,
    )
    parent_state = fields.Selection(
        related="asset_id.state", string="State of Asset", readonly=True
    )
    depreciation_base = fields.Float(
        related="asset_id.depreciation_base", string="Depreciation Base", readonly=True
    )
    amount = fields.Float(string="Amount", digits="Account", required=True)
    remaining_value = fields.Float(
        compute="_compute_values",
        digits="Account",
        string="Next Period Depreciation",
        store=True,
    )
    depreciated_value = fields.Float(
        compute="_compute_values",
        digits="Account",
        string="Amount Already Depreciated",
        store=True,
    )
    line_date = fields.Date(string="Date", required=True)
    line_days = fields.Integer(string="Days", readonly=True)
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Depreciation Entry",
        readonly=True,
        check_company=True,
    )
    move_check = fields.Boolean(
        compute="_compute_move_check", string="Posted", store=True
    )
    type = fields.Selection(
        selection=[
            ("create", "Depreciation Base"),
            ("depreciate", "Depreciation"),
            ("remove", "Asset Removal"),
        ],
        readonly=True,
        default="depreciate",
    )
    init_entry = fields.Boolean(
        string="Initial Balance Entry",
        help="Set this flag for entries of previous fiscal years "
        "for which Odoo has not generated accounting entries.",
    )
    company_id = fields.Many2one(
        "res.company", store=True, readonly=True, related="asset_id.company_id",
    )

    @api.depends("amount", "previous_id", "type")
    def _compute_values(self):
        self.depreciated_value = 0.0
        self.remaining_value = 0.0
        dlines = self
        if self.env.context.get("no_compute_asset_line_ids"):
            # skip compute for lines in unlink
            exclude_ids = self.env.context["no_compute_asset_line_ids"]
            dlines = self.filtered(lambda l: l.id not in exclude_ids)
        dlines = dlines.filtered(lambda l: l.type == "depreciate")
        dlines = dlines.sorted(key=lambda l: l.line_date)
        # Give value 0 to the lines that are not going to be calculated
        # to avoid cache miss error
        all_excluded_lines = self - dlines
        all_excluded_lines.depreciated_value = 0
        all_excluded_lines.remaining_value = 0
        # Group depreciation lines per asset
        asset_ids = dlines.mapped("asset_id")
        grouped_dlines = []
        for asset in asset_ids:
            grouped_dlines.append(dlines.filtered(lambda l: l.asset_id.id == asset.id))
        for dlines in grouped_dlines:
            for i, dl in enumerate(dlines):
                if i == 0:
                    depreciation_base = dl.depreciation_base
                    tmp = depreciation_base - dl.previous_id.remaining_value
                    depreciated_value = dl.previous_id and tmp or 0.0
                    remaining_value = depreciation_base - depreciated_value - dl.amount
                else:
                    depreciated_value += dl.previous_id.amount
                    remaining_value -= dl.amount
                dl.depreciated_value = depreciated_value
                dl.remaining_value = remaining_value

    @api.depends("move_id")
    def _compute_move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    @api.onchange("amount")
    def _onchange_amount(self):
        if self.type == "depreciate":
            self.remaining_value = (
                self.depreciation_base - self.depreciated_value - self.amount
            )

    def write(self, vals):
        for dl in self:
            line_date = vals.get("line_date") or dl.line_date
            asset_lines = dl.asset_id.depreciation_line_ids
            if list(vals.keys()) == ["move_id"] and not vals["move_id"]:
                # allow to remove an accounting entry via the
                # 'Delete Move' button on the depreciation lines.
                if not self.env.context.get("unlink_from_asset"):
                    raise UserError(
                        _(
                            "You are not allowed to remove an accounting entry "
                            "linked to an asset."
                            "\nYou should remove such entries from the asset."
                        )
                    )
            elif list(vals.keys()) == ["asset_id"]:
                continue
            elif (
                dl.move_id
                and not self.env.context.get("allow_asset_line_update")
                and dl.type != "create"
            ):
                raise UserError(
                    _(
                        "You cannot change a depreciation line "
                        "with an associated accounting entry."
                    )
                )
            elif vals.get("init_entry"):
                check = asset_lines.filtered(
                    lambda l: l.move_check
                    and l.type == "depreciate"
                    and l.line_date <= line_date
                )
                if check:
                    raise UserError(
                        _(
                            "You cannot set the 'Initial Balance Entry' flag "
                            "on a depreciation line "
                            "with prior posted entries."
                        )
                    )
            elif vals.get("line_date"):
                if dl.type == "create":
                    check = asset_lines.filtered(
                        lambda l: l.type != "create"
                        and (l.init_entry or l.move_check)
                        and l.line_date < fields.Date.to_date(vals["line_date"])
                    )
                    if check:
                        raise UserError(
                            _(
                                "You cannot set the Asset Start Date "
                                "after already posted entries."
                            )
                        )
                else:
                    check = asset_lines.filtered(
                        lambda al: al != dl
                        and (al.init_entry or al.move_check)
                        and al.line_date > fields.Date.to_date(vals["line_date"])
                    )
                    if check:
                        raise UserError(
                            _(
                                "You cannot set the date on a depreciation line "
                                "prior to already posted entries."
                            )
                        )
        return super().write(vals)

    def unlink(self):
        for dl in self:
            if dl.type == "create" and dl.amount:
                raise UserError(
                    _("You cannot remove an asset line " "of type 'Depreciation Base'.")
                )
            elif dl.move_id:
                raise UserError(
                    _(
                        "You cannot delete a depreciation line with "
                        "an associated accounting entry."
                    )
                )
            previous = dl.previous_id
            next_line = dl.asset_id.depreciation_line_ids.filtered(
                lambda l: l.previous_id == dl and l not in self
            )
            if next_line:
                next_line.previous_id = previous
        return super(
            AccountAssetLine, self.with_context(no_compute_asset_line_ids=self.ids)
        ).unlink()

    def _setup_move_data(self, depreciation_date):
        asset = self.asset_id
        move_data = {
            "date": depreciation_date,
            "ref": "{} - {}".format(asset.name, self.name),
            "journal_id": asset.profile_id.journal_id.id,
        }
        return move_data

    def _setup_move_line_data(self, depreciation_date, account, ml_type, move):
        """Prepare data to be propagated to account.move.line"""
        asset = self.asset_id
        amount = self.amount
        analytic_id = False
        analytic_tags = self.env["account.analytic.tag"]
        if ml_type == "depreciation":
            debit = amount < 0 and -amount or 0.0
            credit = amount > 0 and amount or 0.0
        elif ml_type == "expense":
            debit = amount > 0 and amount or 0.0
            credit = amount < 0 and -amount or 0.0
            analytic_id = asset.account_analytic_id.id
            analytic_tags = asset.analytic_tag_ids
        move_line_data = {
            "name": asset.name,
            "ref": self.name,
            "move_id": move.id,
            "account_id": account.id,
            "credit": credit,
            "debit": debit,
            "journal_id": asset.profile_id.journal_id.id,
            "partner_id": asset.partner_id.id,
            "analytic_account_id": analytic_id,
            "analytic_tag_ids": [(4, tag.id) for tag in analytic_tags],
            "date": depreciation_date,
            "asset_id": asset.id,
        }
        return move_line_data

    def create_move(self):
        created_move_ids = []
        asset_ids = set()
        ctx = dict(self.env.context, allow_asset=True, check_move_validity=False)
        for line in self:
            asset = line.asset_id
            depreciation_date = line.line_date
            am_vals = line._setup_move_data(depreciation_date)
            move = self.env["account.move"].with_context(ctx).create(am_vals)
            depr_acc = asset.profile_id.account_depreciation_id
            exp_acc = asset.profile_id.account_expense_depreciation_id
            aml_d_vals = line._setup_move_line_data(
                depreciation_date, depr_acc, "depreciation", move
            )
            self.env["account.move.line"].with_context(ctx).create(aml_d_vals)
            aml_e_vals = line._setup_move_line_data(
                depreciation_date, exp_acc, "expense", move
            )
            self.env["account.move.line"].with_context(ctx).create(aml_e_vals)
            move.post()
            line.with_context(allow_asset_line_update=True).write({"move_id": move.id})
            created_move_ids.append(move.id)
            asset_ids.add(asset.id)
        # we re-evaluate the assets to determine if we can close them
        for asset in self.env["account.asset"].browse(list(asset_ids)):
            if asset.company_currency_id.is_zero(asset.value_residual):
                asset.state = "close"
        return created_move_ids

    def open_move(self):
        self.ensure_one()
        return {
            "name": _("Journal Entry"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": self.env.context,
            "domain": [("id", "=", self.move_id.id)],
        }

    def update_asset_line_after_unlink_move(self):
        self.write({"move_id": False})
        if self.parent_state == "close":
            self.asset_id.write({"state": "open"})
        elif self.parent_state == "removed" and self.type == "remove":
            self.asset_id.write({"state": "close", "date_remove": False})
            self.unlink()

    def unlink_move(self):
        for line in self:
            if line.asset_id.profile_id.allow_reversal:
                context = dict(self._context or {})
                context.update(
                    {
                        "active_model": self._name,
                        "active_ids": line.ids,
                        "active_id": line.id,
                    }
                )
                return {
                    "name": _("Reverse Move"),
                    "view_mode": "form",
                    "res_model": "wiz.asset.move.reverse",
                    "target": "new",
                    "type": "ir.actions.act_window",
                    "context": context,
                }
            else:
                move = line.move_id
                move.button_draft()
                move.with_context(force_delete=True, unlink_from_asset=True).unlink()
                line.with_context(
                    unlink_from_asset=True
                ).update_asset_line_after_unlink_move()
        return True
