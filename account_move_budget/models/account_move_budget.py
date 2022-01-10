# Copyright 2019 ACSONE SA/NV
# Copyright 2019 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountMoveBudget(models.Model):
    _name = "account.move.budget"
    _description = "Account Move Budget"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(
        required=True,
        tracking=True,
    )
    description = fields.Char(
        tracking=True,
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    date_from = fields.Date(
        required=True,
        string="From Date",
        tracking=True,
    )
    date_to = fields.Date(
        required=True,
        string="To Date",
        tracking=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        required=True,
        default="draft",
        tracking=True,
    )
    line_ids = fields.One2many(
        comodel_name="account.move.budget.line", inverse_name="budget_id", copy=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        if default is None:
            default = {}
        if "name" not in default:
            default["name"] = _("%s (copy)") % self.name
        return super(AccountMoveBudget, self).copy(default=default)

    @api.onchange("date_range_id")
    def _onchange_date_range(self):
        for rec in self:
            if rec.date_range_id:
                rec.date_from = rec.date_range_id.date_start
                rec.date_to = rec.date_range_id.date_end

    @api.onchange("date_from", "date_to")
    def _onchange_dates(self):
        for rec in self:
            if rec.date_range_id:
                if (
                    rec.date_from != rec.date_range_id.date_start
                    or rec.date_to != rec.date_range_id.date_end
                ):
                    rec.date_range_id = False

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_confirm(self):
        for rec in self:
            rec.state = "confirmed"
