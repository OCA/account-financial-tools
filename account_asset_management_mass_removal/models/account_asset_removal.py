# Copyright 2020 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class AccountAssetRemoval(models.Model):
    _name = "account.asset.removal"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Asset Removal Batch"
    _order = "name desc"

    name = fields.Char(
        string="Asset Name",
        required=True,
        readonly=True,
        default="/",
        copy=False,
        tracking=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Prepared By",
        required=True,
        readonly=True,
        default=lambda self: self.env.user,
    )
    date_removal = fields.Date(
        default=lambda self: fields.Date.context_today(self),
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    state = fields.Selection(
        selection=[("draft", "Draft"), ("done", "Removed"), ("cancel", "Cancelled")],
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
    removal_asset_ids = fields.One2many(
        comodel_name="account.asset.removal.line",
        inverse_name="removal_id",
        string="Removing Assets",
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    source_asset_count = fields.Integer(
        string="Assets", compute="_compute_asset_count",
    )
    move_ids = fields.Many2many(
        comodel_name="account.move", string="Journal Entries", readonly=True,
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
            "domain": [("id", "in", self.move_ids.ids)],
        }

    def _compute_asset_count(self):
        for rec in self:
            rec.source_asset_count = len(rec.removal_asset_ids.mapped("asset_id"))

    def open_asset_removed(self):
        self.ensure_one()
        action = self.env.ref("account_asset_management.account_asset_action")
        result = action.read()[0]
        dom = [("id", "in", self.removal_asset_ids.mapped("asset_id").ids)]
        result.update({"domain": dom})
        return result

    @api.model
    def create(self, vals):
        if vals.get("name", "/") == "/":
            vals["name"] = (
                self.env["ir.sequence"]
                .with_context(ir_sequence_date=vals.get("date_removal"))
                .next_by_code("account.asset.removal")
            )
        return super().create(vals)

    def _check_configured_asset(self):
        if self.filtered(lambda l: not l.removal_asset_ids):
            raise UserError(_("You need to add a line before remove assets."))
        return True

    def remove(self):
        """ Call function remove() on account_asset_remove wizard """
        self._check_configured_asset()
        for rec in self:
            move = []
            for line in rec.removal_asset_ids:
                asset_id = line.asset_id
                action_asset = asset_id.remove()
                ctx = action_asset.get("context", False)
                action_remove = line.with_context(ctx).remove()
                # get move_id from action return remove
                domain = action_remove.get("domain", False)
                if domain:
                    move.append(domain[0][2])
            rec.write({"state": "done", "move_ids": move})
        return True

    def set_to_draft(self):
        return self.write({"state": "draft"})

    def cancel(self):
        return self.write({"state": "cancel"})


class AccountAssetRemovalLine(models.Model):
    _name = "account.asset.removal.line"
    _inherit = "account.asset.remove"
    _description = "Asset Removal Lines"
    _transient = False

    removal_id = fields.Many2one(
        comodel_name="account.asset.removal",
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    asset_id = fields.Many2one(
        comodel_name="account.asset",
        domain=[("state", "in", ("open", "close"))],
        required=True,
        ondelete="restrict",
    )

    @api.constrains("sale_value")
    def _check_sale_value(self):
        if self.filtered(lambda l: l.sale_value < 0.0):
            raise ValidationError(_("The Sale Value must be positive!"))

    @api.onchange("asset_id")
    def _onchange_account_value_id(self):
        if self.asset_id:
            self.account_plus_value_id = self.asset_id.profile_id.account_plus_value_id
            self.account_min_value_id = self.asset_id.profile_id.account_min_value_id
            self.account_residual_value_id = (
                self.asset_id.profile_id.account_residual_value_id
            )
