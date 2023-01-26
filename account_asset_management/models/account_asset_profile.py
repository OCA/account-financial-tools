# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAssetProfile(models.Model):
    _name = "account.asset.profile"
    _check_company_auto = True
    _description = "Asset profile"
    _order = "name"

    name = fields.Char(size=64, required=True, index=True)
    note = fields.Text()
    account_analytic_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Analytic account"
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag", string="Analytic tags"
    )
    account_asset_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        string="Asset Account",
        check_company=True,
        required=True,
    )
    account_depreciation_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        string="Depreciation Account",
        check_company=True,
        required=True,
    )
    account_expense_depreciation_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        string="Depr. Expense Account",
        check_company=True,
        required=True,
    )
    account_plus_value_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        string="Plus-Value Account",
    )
    account_min_value_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        string="Min-Value Account",
    )
    account_residual_value_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
        check_company=True,
        string="Residual Value Account",
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
        string="Journal",
        check_company=True,
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        default=lambda self: self._default_company_id(),
    )
    group_ids = fields.Many2many(
        comodel_name="account.asset.group",
        relation="account_asset_profile_group_rel",
        column1="profile_id",
        column2="group_id",
        check_company=True,
        string="Asset Groups",
    )
    salvage_value = fields.Float(
        digits="Account",
        help="The estimated value that an asset will realize upon "
        "its sale at the end of its useful life.\n"
        "This value is used to determine the depreciation amounts.",
    )
    salvage_type = fields.Selection(
        selection=[("fixed", "Fixed"), ("percent", "Percentage of Price")]
    )
    method = fields.Selection(
        selection=lambda self: self._selection_method(),
        string="Computation Method",
        required=True,
        help="Choose the method to use to compute the depreciation lines.\n"
        "  * Linear: Calculated on basis of: "
        "Depreciation Base / Number of Depreciations. "
        "Depreciation Base = Purchase Value - Salvage Value.\n"
        "  * Linear-Limit: Linear up to Salvage Value. "
        "Depreciation Base = Purchase Value.\n"
        "  * Degressive: Calculated on basis of: "
        "Residual Value * Degressive Factor.\n"
        "  * Degressive-Linear (only for Time Method = Year): "
        "Degressive becomes linear when the annual linear "
        "depreciation exceeds the annual degressive depreciation.\n"
        "   * Degressive-Limit: Degressive up to Salvage Value. "
        "The Depreciation Base is equal to the asset value.",
        default="linear",
    )
    method_number = fields.Integer(
        string="Number of Years",
        help="The number of years needed to depreciate your asset",
        default=5,
    )
    method_period = fields.Selection(
        selection=lambda self: self._selection_method_period(),
        string="Period Length",
        required=True,
        default="year",
        help="Period length for the depreciation accounting entries",
    )
    method_progress_factor = fields.Float(string="Degressive Factor", default=0.3)
    method_time = fields.Selection(
        selection=lambda self: self._selection_method_time(),
        string="Time Method",
        required=True,
        default="year",
        help="Choose the method to use to compute the dates and "
        "number of depreciation lines.\n"
        "  * Number of Years: Specify the number of years "
        "for the depreciation.\n"
        "  * Number of Depreciations: Fix the number of "
        "depreciation lines and the time between 2 depreciations.\n",
    )
    days_calc = fields.Boolean(
        string="Calculate by days",
        default=False,
        help="Use number of days to calculate depreciation amount",
    )
    use_leap_years = fields.Boolean(
        default=False,
        help="If not set, the system will distribute evenly the amount to "
        "amortize across the years, based on the number of years. "
        "So the amount per year will be the "
        "depreciation base / number of years.\n "
        "If set, the system will consider if the current year "
        "is a leap year. The amount to depreciate per year will be "
        "calculated as depreciation base / (depreciation end date - "
        "start date + 1) * days in the current year.",
    )
    prorata = fields.Boolean(
        string="Prorata Temporis",
        compute="_compute_prorrata",
        readonly=False,
        store=True,
        help="Indicates that the first depreciation entry for this asset "
        "has to be done from the depreciation start date instead of "
        "the first day of the fiscal year.",
    )
    open_asset = fields.Boolean(
        string="Skip Draft State",
        help="Check this if you want to automatically confirm the assets "
        "of this profile when created by invoices.",
    )
    asset_product_item = fields.Boolean(
        string="Create an asset by product item",
        help="By default during the validation of an invoice, an asset "
        "is created by invoice line as long as an accounting entry is "
        "created by invoice line. "
        "With this setting, an accounting entry will be created by "
        "product item. So, there will be an asset by product item.",
    )
    active = fields.Boolean(default=True)
    allow_reversal = fields.Boolean(
        "Allow Reversal of journal entries",
        help="If set, when pressing the Delete/Reverse Move button in a "
        "posted depreciation line will prompt the option to reverse the "
        "journal entry, instead of deleting them.",
    )

    @api.model
    def _default_company_id(self):
        return self.env.company

    @api.model
    def _selection_method(self):
        return [
            ("linear", _("Linear")),
            ("linear-limit", _("Linear up to Salvage Value")),
            ("degressive", _("Degressive")),
            ("degr-linear", _("Degressive-Linear")),
            ("degr-limit", _("Degressive  up to Salvage Value")),
        ]

    @api.model
    def _selection_method_period(self):
        return [("month", _("Month")), ("quarter", _("Quarter")), ("year", _("Year"))]

    @api.model
    def _selection_method_time(self):
        return [
            ("year", _("Number of Years or end date")),
            ("number", _("Number of Depreciations")),
        ]

    @api.constrains("method", "method_time")
    def _check_method(self):
        if any(a.method == "degr-linear" and a.method_time != "year" for a in self):
            raise UserError(
                _("Degressive-Linear is only supported for Time Method = Year.")
            )

    @api.depends("method_time")
    def _compute_prorrata(self):
        for profile in self:
            if profile.method_time != "year":
                profile.prorata = True

    @api.model
    def create(self, vals):
        if vals.get("method_time") != "year" and not vals.get("prorata"):
            vals["prorata"] = True
        profile = super().create(vals)
        acc_id = vals.get("account_asset_id")
        if acc_id:
            account = self.env["account.account"].browse(acc_id)
            if not account.asset_profile_id:
                account.write({"asset_profile_id": profile.id})
        return profile

    def write(self, vals):
        if vals.get("method_time"):
            if vals["method_time"] != "year" and not vals.get("prorata"):
                vals["prorata"] = True
        res = super().write(vals)
        # TODO last profile in self is defined as default on the related
        # account. must be improved.
        account = self.env["account.account"].browse(vals.get("account_asset_id"))
        if self and account and not account.asset_profile_id:
            account.write({"asset_profile_id": self[-1].id})
        return res
