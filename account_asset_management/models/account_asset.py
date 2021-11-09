# Copyright 2009-2018 Noviat
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
import logging
from datetime import date
from functools import reduce
from sys import exc_info
from traceback import format_exception

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

READONLY_STATES = {
    "open": [("readonly", True)],
    "close": [("readonly", True)],
    "removed": [("readonly", True)],
}


class DummyFy(object):
    def __init__(self, *args, **argv):
        for key, arg in argv.items():
            setattr(self, key, arg)


class AccountAsset(models.Model):
    _name = "account.asset"
    _description = "Asset"
    _order = "date_start desc, code, name"
    _check_company_auto = True

    account_move_line_ids = fields.One2many(
        comodel_name="account.move.line",
        inverse_name="asset_id",
        string="Entries",
        readonly=True,
        copy=False,
        check_company=True,
    )
    move_line_check = fields.Boolean(
        compute="_compute_move_line_check", string="Has accounting entries"
    )
    name = fields.Char(
        string="Asset Name",
        required=True,
        states=READONLY_STATES,
    )
    code = fields.Char(
        string="Reference",
        size=32,
        states=READONLY_STATES,
    )
    purchase_value = fields.Float(
        string="Purchase Value",
        required=True,
        states=READONLY_STATES,
        help="This amount represent the initial value of the asset."
        "\nThe Depreciation Base is calculated as follows:"
        "\nPurchase Value - Salvage Value.",
    )
    salvage_value = fields.Float(
        string="Salvage Value",
        digits="Account",
        states=READONLY_STATES,
        help="The estimated value that an asset will realize upon "
        "its sale at the end of its useful life.\n"
        "This value is used to determine the depreciation amounts.",
    )
    depreciation_base = fields.Float(
        compute="_compute_depreciation_base",
        digits="Account",
        string="Depreciation Base",
        store=True,
        help="This amount represent the depreciation base "
        "of the asset (Purchase Value - Salvage Value).",
    )
    value_residual = fields.Float(
        compute="_compute_depreciation",
        digits="Account",
        string="Residual Value",
        store=True,
    )
    value_depreciated = fields.Float(
        compute="_compute_depreciation",
        digits="Account",
        string="Depreciated Value",
        store=True,
    )
    note = fields.Text("Note")
    profile_id = fields.Many2one(
        comodel_name="account.asset.profile",
        string="Asset Profile",
        change_default=True,
        required=True,
        states=READONLY_STATES,
        check_company=True,
    )
    group_ids = fields.Many2many(
        comodel_name="account.asset.group",
        compute="_compute_group_ids",
        readonly=False,
        store=True,
        relation="account_asset_group_rel",
        column1="asset_id",
        column2="group_id",
        string="Asset Groups",
    )
    date_start = fields.Date(
        string="Asset Start Date",
        required=True,
        states=READONLY_STATES,
        help="You should manually add depreciation lines "
        "with the depreciations of previous fiscal years "
        "if the Depreciation Start Date is different from the date "
        "for which accounting entries need to be generated.",
    )
    date_remove = fields.Date(string="Asset Removal Date", readonly=True)
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Running"),
            ("close", "Close"),
            ("removed", "Removed"),
        ],
        string="Status",
        required=True,
        default="draft",
        copy=False,
        help="When an asset is created, the status is 'Draft'.\n"
        "If the asset is confirmed, the status goes in 'Running' "
        "and the depreciation lines can be posted "
        "to the accounting.\n"
        "If the last depreciation line is posted, "
        "the asset goes into the 'Close' status.\n"
        "When the removal entries are generated, "
        "the asset goes into the 'Removed' status.",
    )
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        states=READONLY_STATES,
    )
    method = fields.Selection(
        selection=lambda self: self.env["account.asset.profile"]._selection_method(),
        string="Computation Method",
        compute="_compute_method",
        readonly=False,
        store=True,
        states=READONLY_STATES,
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
    )
    method_number = fields.Integer(
        string="Number of Years",
        compute="_compute_method_number",
        readonly=False,
        store=True,
        states=READONLY_STATES,
        help="The number of years needed to depreciate your asset",
    )
    method_period = fields.Selection(
        selection=lambda self: self.env[
            "account.asset.profile"
        ]._selection_method_period(),
        string="Period Length",
        compute="_compute_method_period",
        readonly=False,
        store=True,
        states=READONLY_STATES,
        help="Period length for the depreciation accounting entries",
    )
    method_end = fields.Date(
        string="Ending Date",
        compute="_compute_method_end",
        readonly=False,
        store=True,
        states=READONLY_STATES,
    )
    method_progress_factor = fields.Float(
        string="Degressive Factor",
        compute="_compute_method_progress_factor",
        readonly=False,
        store=True,
        states=READONLY_STATES,
    )
    method_time = fields.Selection(
        selection=lambda self: self.env[
            "account.asset.profile"
        ]._selection_method_time(),
        string="Time Method",
        compute="_compute_method_time",
        readonly=False,
        store=True,
        states=READONLY_STATES,
        help="Choose the method to use to compute the dates and "
        "number of depreciation lines.\n"
        "  * Number of Years: Specify the number of years "
        "for the depreciation.\n"
        "  * Number of Depreciations: Fix the number of "
        "depreciation lines and the time between 2 depreciations.\n",
    )
    days_calc = fields.Boolean(
        string="Calculate by days",
        compute="_compute_days_calc",
        readonly=False,
        store=True,
        help="Use number of days to calculate depreciation amount",
    )
    use_leap_years = fields.Boolean(
        string="Use leap years",
        compute="_compute_use_leap_years",
        readonly=False,
        store=True,
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
        states=READONLY_STATES,
        help="Indicates that the first depreciation entry for this asset "
        "has to be done from the depreciation start date instead of "
        "the first day of the fiscal year.",
    )
    depreciation_line_ids = fields.One2many(
        comodel_name="account.asset.line",
        inverse_name="asset_id",
        string="Depreciation Lines",
        copy=False,
        states=READONLY_STATES,
        check_company=True,
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
        string="Company Currency",
        store=True,
        readonly=True,
    )
    account_analytic_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic account",
        compute="_compute_account_analytic_id",
        readonly=False,
        store=True,
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name="account.analytic.tag",
        string="Analytic tags",
        compute="_compute_analytic_tag_ids",
        readonly=False,
        store=True,
    )

    @api.model
    def _default_company_id(self):
        return self.env.company

    @api.depends("depreciation_line_ids.move_id")
    def _compute_move_line_check(self):
        for asset in self:
            asset.move_line_check = bool(
                asset.depreciation_line_ids.filtered("move_id")
            )

    @api.depends("purchase_value", "salvage_value", "method")
    def _compute_depreciation_base(self):
        for asset in self:
            if asset.method in ["linear-limit", "degr-limit"]:
                asset.depreciation_base = asset.purchase_value
            else:
                asset.depreciation_base = asset.purchase_value - asset.salvage_value

    @api.depends(
        "depreciation_base",
        "depreciation_line_ids.type",
        "depreciation_line_ids.amount",
        "depreciation_line_ids.previous_id",
        "depreciation_line_ids.init_entry",
        "depreciation_line_ids.move_check",
    )
    def _compute_depreciation(self):
        for asset in self:
            lines = asset.depreciation_line_ids.filtered(
                lambda l: l.type in ("depreciate", "remove")
                and (l.init_entry or l.move_check)
            )
            value_depreciated = sum([line.amount for line in lines])
            residual = asset.depreciation_base - value_depreciated
            depreciated = value_depreciated
            asset.update({"value_residual": residual, "value_depreciated": depreciated})

    @api.depends("profile_id")
    def _compute_group_ids(self):
        for asset in self:
            if asset.profile_id:
                asset.group_ids = asset.profile_id.group_ids

    @api.depends("profile_id")
    def _compute_method(self):
        for asset in self:
            asset.method = asset.profile_id.method

    @api.depends("profile_id", "method_end")
    def _compute_method_number(self):
        for asset in self:
            if asset.method_end:
                asset.method_number = 0
            else:
                asset.method_number = asset.profile_id.method_number

    @api.depends("profile_id")
    def _compute_method_period(self):
        for asset in self:
            asset.method_period = asset.profile_id.method_period

    @api.depends("method_number")
    def _compute_method_end(self):
        for asset in self:
            if asset.method_number:
                asset.method_end = False

    @api.depends("profile_id")
    def _compute_method_progress_factor(self):
        for asset in self:
            asset.method_progress_factor = asset.profile_id.method_progress_factor

    @api.depends("profile_id")
    def _compute_method_time(self):
        for asset in self:
            asset.method_time = asset.profile_id.method_time

    @api.depends("profile_id")
    def _compute_days_calc(self):
        for asset in self:
            asset.days_calc = asset.profile_id.days_calc

    @api.depends("profile_id")
    def _compute_use_leap_years(self):
        for asset in self:
            asset.use_leap_years = asset.profile_id.use_leap_years

    @api.depends("profile_id", "method_time")
    def _compute_prorrata(self):
        for asset in self:
            if asset.method_time != "year":
                asset.prorata = True
            else:
                asset.prorata = asset.profile_id.prorata

    @api.depends("profile_id")
    def _compute_account_analytic_id(self):
        for asset in self:
            asset.account_analytic_id = asset.profile_id.account_analytic_id

    @api.depends("profile_id")
    def _compute_analytic_tag_ids(self):
        for asset in self:
            asset.analytic_tag_ids = asset.profile_id.analytic_tag_ids

    @api.constrains("method", "method_time")
    def _check_method(self):
        if self.filtered(
            lambda a: a.method == "degr-linear" and a.method_time != "year"
        ):
            raise UserError(
                _("Degressive-Linear is only supported for Time Method = Year.")
            )

    @api.constrains("date_start", "method_end", "method_number", "method_time")
    def _check_dates(self):
        if self.filtered(
            lambda a: a.method_time == "year"
            and not a.method_number
            and a.method_end
            and a.method_end <= a.date_start
        ):
            raise UserError(_("The Start Date must precede the Ending Date."))

    @api.constrains("profile_id")
    def _check_profile_change(self):
        if self.depreciation_line_ids.filtered("move_id"):
            raise UserError(
                _(
                    "You cannot change the profile of an asset "
                    "with accounting entries."
                )
            )

    @api.onchange("purchase_value", "salvage_value", "date_start", "method")
    def _onchange_purchase_salvage_value(self):
        if self.method in ["linear-limit", "degr-limit"]:
            self.depreciation_base = self.purchase_value or 0.0
        else:
            purchase_value = self.purchase_value or 0.0
            salvage_value = self.salvage_value or 0.0
            self.depreciation_base = purchase_value - salvage_value
        dl_create_line = self.depreciation_line_ids.filtered(
            lambda r: r.type == "create"
        )
        if dl_create_line:
            dl_create_line.update(
                {"amount": self.depreciation_base, "line_date": self.date_start}
            )

    @api.model
    def create(self, vals):
        asset = super().create(vals)
        if self.env.context.get("create_asset_from_move_line"):
            # Trigger compute of depreciation_base
            asset.salvage_value = 0.0
        asset._create_first_asset_line()
        return asset

    def write(self, vals):
        res = super().write(vals)
        for asset in self:
            if self.env.context.get("asset_validate_from_write"):
                continue
            asset._create_first_asset_line()
            if asset.profile_id.open_asset and self.env.context.get(
                "create_asset_from_move_line"
            ):
                asset.compute_depreciation_board()
                # extra context to avoid recursion
                asset.with_context(asset_validate_from_write=True).validate()
        return res

    def _create_first_asset_line(self):
        self.ensure_one()
        if self.depreciation_base and not self.depreciation_line_ids:
            asset_line_obj = self.env["account.asset.line"]
            line_name = self._get_depreciation_entry_name(0)
            asset_line_vals = {
                "amount": self.depreciation_base,
                "asset_id": self.id,
                "name": line_name,
                "line_date": self.date_start,
                "init_entry": True,
                "type": "create",
            }
            asset_line = asset_line_obj.create(asset_line_vals)
            if self.env.context.get("create_asset_from_move_line"):
                asset_line.move_id = self.env.context["move_id"]

    def unlink(self):
        for asset in self:
            if asset.state != "draft":
                raise UserError(_("You can only delete assets in draft state."))
            if asset.depreciation_line_ids.filtered(
                lambda r: r.type == "depreciate" and r.move_check
            ):
                raise UserError(
                    _(
                        "You cannot delete an asset that contains "
                        "posted depreciation lines."
                    )
                )
        # update accounting entries linked to lines of type 'create'
        amls = self.with_context(allow_asset_removal=True).mapped(
            "account_move_line_ids"
        )
        amls.write({"asset_id": False})
        return super().unlink()

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = ["|", ("code", "=ilike", name + "%"), ("name", operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        assets = self.search(domain + args, limit=limit)
        return assets.name_get()

    @api.depends("name", "code")
    def name_get(self):
        result = []
        for asset in self:
            name = asset.name
            if asset.code:
                name = " - ".join([asset.code, name])
            result.append((asset.id, name))
        return result

    def validate(self):
        for asset in self:
            if asset.company_currency_id.is_zero(asset.value_residual):
                asset.state = "close"
            else:
                asset.state = "open"
                if not asset.depreciation_line_ids.filtered(
                    lambda l: l.type != "create"
                ):
                    asset.compute_depreciation_board()
        return True

    def remove(self):
        self.ensure_one()
        ctx = dict(self.env.context, active_ids=self.ids, active_id=self.id)

        early_removal = False
        if self.method in ["linear-limit", "degr-limit"]:
            if self.value_residual != self.salvage_value:
                early_removal = True
        elif self.value_residual:
            early_removal = True
        if early_removal:
            ctx.update({"early_removal": True})

        return {
            "name": _("Generate Asset Removal entries"),
            "view_mode": "form",
            "res_model": "account.asset.remove",
            "target": "new",
            "type": "ir.actions.act_window",
            "context": ctx,
        }

    def set_to_draft(self):
        return self.write({"state": "draft"})

    def open_entries(self):
        self.ensure_one()
        # needed for avoiding errors after grouping in assets
        context = dict(self.env.context)
        context.pop("group_by", None)
        return {
            "name": _("Journal Entries"),
            "view_mode": "tree,form",
            "res_model": "account.move",
            "view_id": False,
            "type": "ir.actions.act_window",
            "context": context,
            "domain": [("id", "in", self.account_move_line_ids.mapped("move_id").ids)],
        }

    def _group_lines(self, table):
        """group lines prior to depreciation start period."""

        def group_lines(x, y):
            y.update({"amount": x["amount"] + y["amount"]})
            return y

        depreciation_start_date = self.date_start
        lines = table[0]["lines"]
        lines1 = []
        lines2 = []
        flag = lines[0]["date"] < depreciation_start_date
        for line in lines:
            if flag:
                lines1.append(line)
                if line["date"] >= depreciation_start_date:
                    flag = False
            else:
                lines2.append(line)
        if lines1:
            lines1 = [reduce(group_lines, lines1)]
            lines1[0]["depreciated_value"] = 0.0
        table[0]["lines"] = lines1 + lines2

    def _compute_depreciation_line(
        self,
        depreciated_value_posted,
        table_i_start,
        line_i_start,
        table,
        last_line,
        posted_lines,
    ):
        digits = self.env["decimal.precision"].precision_get("Account")
        company = self.company_id
        fiscalyear_lock_date = company.fiscalyear_lock_date or fields.Date.to_date(
            "1901-01-01"
        )

        seq = len(posted_lines)
        depr_line = last_line
        last_date = table[-1]["lines"][-1]["date"]
        depreciated_value = depreciated_value_posted
        for entry in table[table_i_start:]:
            for line in entry["lines"][line_i_start:]:
                seq += 1
                name = self._get_depreciation_entry_name(seq)
                amount = line["amount"]
                if line["date"] == last_date:
                    # ensure that the last entry of the table always
                    # depreciates the remaining value
                    amount = self.depreciation_base - depreciated_value
                    if self.method in ["linear-limit", "degr-limit"]:
                        amount -= self.salvage_value
                if amount:
                    vals = {
                        "previous_id": depr_line.id,
                        "amount": round(amount, digits),
                        "asset_id": self.id,
                        "name": name,
                        "line_date": line["date"],
                        "line_days": line["days"],
                        "init_entry": fiscalyear_lock_date >= line["date"],
                    }
                    depreciated_value += round(amount, digits)
                    depr_line = self.env["account.asset.line"].create(vals)
                else:
                    seq -= 1
            line_i_start = 0

    def compute_depreciation_board(self):

        line_obj = self.env["account.asset.line"]
        digits = self.env["decimal.precision"].precision_get("Account")

        for asset in self:
            if asset.value_residual == 0.0:
                continue
            domain = [
                ("asset_id", "=", asset.id),
                ("type", "=", "depreciate"),
                "|",
                ("move_check", "=", True),
                ("init_entry", "=", True),
            ]
            posted_lines = line_obj.search(domain, order="line_date desc")
            if posted_lines:
                last_line = posted_lines[0]
            else:
                last_line = line_obj
            domain = [
                ("asset_id", "=", asset.id),
                ("type", "=", "depreciate"),
                ("move_id", "=", False),
                ("init_entry", "=", False),
            ]
            old_lines = line_obj.search(domain)
            if old_lines:
                old_lines.unlink()

            table = asset._compute_depreciation_table()
            if not table:
                continue

            asset._group_lines(table)

            # check table with posted entries and
            # recompute in case of deviation
            depreciated_value_posted = depreciated_value = 0.0
            if posted_lines:
                total_table_lines = sum([len(entry["lines"]) for entry in table])
                move_check_lines = asset.depreciation_line_ids.filtered("move_check")
                last_depreciation_date = last_line.line_date
                last_date_in_table = table[-1]["lines"][-1]["date"]
                # If the number of lines in the table is the same as the depreciation
                # lines, we will not show an error even if the dates are the same.
                if (last_date_in_table < last_depreciation_date) or (
                    last_date_in_table == last_depreciation_date
                    and total_table_lines != len(move_check_lines)
                ):
                    raise UserError(
                        _(
                            "The duration of the asset conflicts with the "
                            "posted depreciation table entry dates."
                        )
                    )

                for _table_i, entry in enumerate(table):
                    residual_amount_table = entry["lines"][-1]["remaining_value"]
                    if (
                        entry["date_start"]
                        <= last_depreciation_date
                        <= entry["date_stop"]
                    ):
                        break

                if entry["date_stop"] == last_depreciation_date:
                    _table_i += 1
                    _line_i = 0
                else:
                    entry = table[_table_i]
                    date_min = entry["date_start"]
                    for _line_i, line in enumerate(entry["lines"]):
                        residual_amount_table = line["remaining_value"]
                        if date_min <= last_depreciation_date <= line["date"]:
                            break
                        date_min = line["date"]
                    if line["date"] == last_depreciation_date:
                        _line_i += 1
                table_i_start = _table_i
                line_i_start = _line_i

                # check if residual value corresponds with table
                # and adjust table when needed
                depreciated_value_posted = depreciated_value = sum(
                    [posted_line.amount for posted_line in posted_lines]
                )
                residual_amount = asset.depreciation_base - depreciated_value
                amount_diff = round(residual_amount_table - residual_amount, digits)
                if amount_diff:
                    # We will auto-create a new line because the number of lines in
                    # the tables are the same as the posted depreciations and there
                    # is still a residual value. Only in this case we will need to
                    # add a new line to the table with the amount of the difference.
                    if len(move_check_lines) == total_table_lines:
                        table[table_i_start]["lines"].append(
                            table[table_i_start]["lines"][line_i_start - 1]
                        )
                        line = table[table_i_start]["lines"][line_i_start]
                        line["days"] = 0
                        line["amount"] = amount_diff
                    # compensate in first depreciation entry
                    # after last posting
                    line = table[table_i_start]["lines"][line_i_start]
                    line["amount"] -= amount_diff

            else:  # no posted lines
                table_i_start = 0
                line_i_start = 0

            asset._compute_depreciation_line(
                depreciated_value_posted,
                table_i_start,
                line_i_start,
                table,
                last_line,
                posted_lines,
            )
        return True

    def _get_fy_duration(self, fy, option="days"):
        """Returns fiscal year duration.

        @param option:
        - days: duration in days
        - months: duration in months,
                  a started month is counted as a full month
        - years: duration in calendar years, considering also leap years
        """
        fy_date_start = fy.date_from
        fy_date_stop = fy.date_to
        days = (fy_date_stop - fy_date_start).days + 1
        months = (
            (fy_date_stop.year - fy_date_start.year) * 12
            + (fy_date_stop.month - fy_date_start.month)
            + 1
        )
        if option == "days":
            return days
        elif option == "months":
            return months
        elif option == "years":
            year = fy_date_start.year
            cnt = fy_date_stop.year - fy_date_start.year + 1
            for i in range(cnt):
                cy_days = calendar.isleap(year) and 366 or 365
                if i == 0:  # first year
                    if fy_date_stop.year == year:
                        duration = (fy_date_stop - fy_date_start).days + 1
                    else:
                        duration = (date(year, 12, 31) - fy_date_start).days + 1
                    factor = float(duration) / cy_days
                elif i == cnt - 1:  # last year
                    duration = (fy_date_stop - date(year, 1, 1)).days + 1
                    factor += float(duration) / cy_days
                else:
                    factor += 1.0
                year += 1
            return factor

    def _get_fy_duration_factor(self, entry, firstyear):
        """
        localization: override this method to change the logic used to
        calculate the impact of extended/shortened fiscal years
        """
        duration_factor = 1.0
        fy = entry["fy"]
        if self.prorata:
            if firstyear:
                depreciation_date_start = self.date_start
                fy_date_stop = entry["date_stop"]
                first_fy_asset_days = (fy_date_stop - depreciation_date_start).days + 1
                first_fy_duration = self._get_fy_duration(fy, option="days")
                first_fy_year_factor = self._get_fy_duration(fy, option="years")
                duration_factor = (
                    float(first_fy_asset_days)
                    / first_fy_duration
                    * first_fy_year_factor
                )
            else:
                duration_factor = self._get_fy_duration(fy, option="years")
        else:
            fy_months = self._get_fy_duration(fy, option="months")
            duration_factor = float(fy_months) / 12
        return duration_factor

    def _get_depreciation_start_date(self, fy):
        """
        In case of 'Linear': the first month is counted as a full month
        if the fiscal year starts in the middle of a month.
        """
        if self.prorata:
            depreciation_start_date = self.date_start
        else:
            depreciation_start_date = fy.date_from
        return depreciation_start_date

    def _get_depreciation_stop_date(self, depreciation_start_date):
        if self.method_time == "year" and not self.method_end:
            depreciation_stop_date = depreciation_start_date + relativedelta(
                years=self.method_number, days=-1
            )
        elif self.method_time == "number":
            if self.method_period == "month":
                depreciation_stop_date = depreciation_start_date + relativedelta(
                    months=self.method_number, days=-1
                )
            elif self.method_period == "quarter":
                m = [x for x in [3, 6, 9, 12] if x >= depreciation_start_date.month][0]
                first_line_date = depreciation_start_date + relativedelta(
                    month=m, day=31
                )
                months = self.method_number * 3
                depreciation_stop_date = first_line_date + relativedelta(
                    months=months - 1, days=-1
                )
            elif self.method_period == "year":
                depreciation_stop_date = depreciation_start_date + relativedelta(
                    years=self.method_number, days=-1
                )
        elif self.method_time == "year" and self.method_end:
            depreciation_stop_date = self.method_end
        return depreciation_stop_date

    def _get_first_period_amount(
        self, table, entry, depreciation_start_date, line_dates
    ):
        """
        Return prorata amount for Time Method 'Year' in case of
        'Prorata Temporis'
        """
        amount = entry.get("period_amount")
        if self.prorata and self.method_time == "year":
            dates = [x for x in line_dates if x <= entry["date_stop"]]
            full_periods = len(dates) - 1
            amount = entry["fy_amount"] - amount * full_periods
        return amount

    def _get_amount_linear(
        self, depreciation_start_date, depreciation_stop_date, entry
    ):
        """
        Override this method if you want to compute differently the
        yearly amount.
        """
        if not self.use_leap_years and self.method_number:
            return self.depreciation_base / self.method_number
        year = entry["date_stop"].year
        cy_days = calendar.isleap(year) and 366 or 365
        days = (depreciation_stop_date - depreciation_start_date).days + 1
        return (self.depreciation_base / days) * cy_days

    def _compute_year_amount(
        self, residual_amount, depreciation_start_date, depreciation_stop_date, entry
    ):
        """
        Localization: override this method to change the degressive-linear
        calculation logic according to local legislation.
        """
        if self.method_time != "year":
            raise UserError(
                _(
                    "The '_compute_year_amount' method is only intended for "
                    "Time Method 'Number of Years'."
                )
            )
        year_amount_linear = self._get_amount_linear(
            depreciation_start_date, depreciation_stop_date, entry
        )
        if self.method == "linear":
            return year_amount_linear
        if self.method == "linear-limit":
            if (residual_amount - year_amount_linear) < self.salvage_value:
                return residual_amount - self.salvage_value
            else:
                return year_amount_linear
        year_amount_degressive = residual_amount * self.method_progress_factor
        if self.method == "degressive":
            return year_amount_degressive
        if self.method == "degr-linear":
            if year_amount_linear > year_amount_degressive:
                return min(year_amount_linear, residual_amount)
            else:
                return min(year_amount_degressive, residual_amount)
        if self.method == "degr-limit":
            if (residual_amount - year_amount_degressive) < self.salvage_value:
                return residual_amount - self.salvage_value
            else:
                return year_amount_degressive
        else:
            raise UserError(_("Illegal value %s in asset.method.") % self.method)

    def _compute_line_dates(self, table, start_date, stop_date):
        """
        The posting dates of the accounting entries depend on the
        chosen 'Period Length' as follows:
        - month: last day of the month
        - quarter: last of the quarter
        - year: last day of the fiscal year

        Override this method if another posting date logic is required.
        """
        line_dates = []

        if self.method_period == "month":
            line_date = start_date + relativedelta(day=31)
        if self.method_period == "quarter":
            m = [x for x in [3, 6, 9, 12] if x >= start_date.month][0]
            line_date = start_date + relativedelta(month=m, day=31)
        elif self.method_period == "year":
            line_date = table[0]["date_stop"]

        i = 1
        while line_date < stop_date:
            line_dates.append(line_date)
            if self.method_period == "month":
                line_date = line_date + relativedelta(months=1, day=31)
            elif self.method_period == "quarter":
                line_date = line_date + relativedelta(months=3, day=31)
            elif self.method_period == "year":
                line_date = table[i]["date_stop"]
                i += 1

        # last entry
        if not (self.method_time == "number" and len(line_dates) == self.method_number):
            if self.days_calc:
                line_dates.append(stop_date)
            else:
                line_dates.append(line_date)

        return line_dates

    def _compute_depreciation_amount_per_fiscal_year(
        self, table, line_dates, depreciation_start_date, depreciation_stop_date
    ):
        digits = self.env["decimal.precision"].precision_get("Account")
        fy_residual_amount = self.depreciation_base
        i_max = len(table) - 1
        asset_sign = self.depreciation_base >= 0 and 1 or -1
        day_amount = 0.0
        if self.days_calc:
            days = (depreciation_stop_date - depreciation_start_date).days + 1
            day_amount = self.depreciation_base / days

        for i, entry in enumerate(table):
            if self.method_time == "year":
                year_amount = self._compute_year_amount(
                    fy_residual_amount,
                    depreciation_start_date,
                    depreciation_stop_date,
                    entry,
                )
                if self.method_period == "year":
                    period_amount = year_amount
                elif self.method_period == "quarter":
                    period_amount = year_amount / 4
                elif self.method_period == "month":
                    period_amount = year_amount / 12
                if i == i_max:
                    if self.method in ["linear-limit", "degr-limit"]:
                        fy_amount = fy_residual_amount - self.salvage_value
                    else:
                        fy_amount = fy_residual_amount
                else:
                    firstyear = i == 0 and True or False
                    fy_factor = self._get_fy_duration_factor(entry, firstyear)
                    fy_amount = year_amount * fy_factor
                if asset_sign * (fy_amount - fy_residual_amount) > 0:
                    fy_amount = fy_residual_amount
                period_amount = round(period_amount, digits)
                fy_amount = round(fy_amount, digits)
            else:
                fy_amount = False
                if self.method_time == "number":
                    number = self.method_number
                else:
                    number = len(line_dates)
                period_amount = round(self.depreciation_base / number, digits)
            entry.update(
                {
                    "period_amount": period_amount,
                    "fy_amount": fy_amount,
                    "day_amount": day_amount,
                }
            )
            if self.method_time == "year":
                fy_residual_amount -= fy_amount
                if round(fy_residual_amount, digits) == 0:
                    break
        i_max = i
        table = table[: i_max + 1]
        return table

    def _compute_depreciation_table_lines(
        self, table, depreciation_start_date, depreciation_stop_date, line_dates
    ):

        digits = self.env["decimal.precision"].precision_get("Account")
        asset_sign = 1 if self.depreciation_base >= 0 else -1
        i_max = len(table) - 1
        remaining_value = self.depreciation_base
        depreciated_value = 0.0
        company = self.company_id
        fiscalyear_lock_date = company.fiscalyear_lock_date or fields.Date.to_date(
            "1901-01-01"
        )

        for i, entry in enumerate(table):

            lines = []
            fy_amount_check = 0.0
            fy_amount = entry["fy_amount"]
            li_max = len(line_dates) - 1
            prev_date = max(entry["date_start"], depreciation_start_date)
            for li, line_date in enumerate(line_dates):
                line_days = (line_date - prev_date).days + 1
                if round(remaining_value, digits) == 0.0:
                    break

                if line_date > min(entry["date_stop"], depreciation_stop_date) and not (
                    i == i_max and li == li_max
                ):
                    prev_date = line_date
                    break
                else:
                    prev_date = line_date + relativedelta(days=1)

                if (
                    self.method == "degr-linear"
                    and asset_sign * (fy_amount - fy_amount_check) < 0
                ):
                    break

                if i == 0 and li == 0:
                    if entry.get("day_amount") > 0.0:
                        amount = line_days * entry.get("day_amount")
                    else:
                        amount = self._get_first_period_amount(
                            table, entry, depreciation_start_date, line_dates
                        )
                        amount = round(amount, digits)
                else:
                    if entry.get("day_amount") > 0.0:
                        amount = line_days * entry.get("day_amount")
                    else:
                        amount = entry.get("period_amount")

                # last year, last entry
                # Handle rounding deviations.
                if i == i_max and li == li_max:
                    amount = remaining_value
                    remaining_value = 0.0
                else:
                    remaining_value -= amount
                fy_amount_check += amount
                line = {
                    "date": line_date,
                    "days": line_days,
                    "amount": amount,
                    "depreciated_value": depreciated_value,
                    "remaining_value": remaining_value,
                    "init": fiscalyear_lock_date >= line_date,
                }
                lines.append(line)
                depreciated_value += amount

            # Handle rounding and extended/shortened FY deviations.
            #
            # Remark:
            # In account_asset_management version < 8.0.2.8.0
            # the FY deviation for the first FY
            # was compensated in the first FY depreciation line.
            # The code has now been simplified with compensation
            # always in last FT depreciation line.
            if self.method_time == "year" and not entry.get("day_amount"):
                if round(fy_amount_check - fy_amount, digits) != 0:
                    diff = fy_amount_check - fy_amount
                    amount = amount - diff
                    remaining_value += diff
                    lines[-1].update(
                        {"amount": amount, "remaining_value": remaining_value}
                    )
                    depreciated_value -= diff

            if not lines:
                table.pop(i)
            else:
                entry["lines"] = lines
            line_dates = line_dates[li:]

        for entry in table:
            if not entry["fy_amount"]:
                entry["fy_amount"] = sum([line["amount"] for line in entry["lines"]])

    def _get_fy_info(self, date):
        """Return an homogeneus data structure for fiscal years."""
        fy_info = self.company_id.compute_fiscalyear_dates(date)
        if "record" not in fy_info:
            fy_info["record"] = DummyFy(
                date_from=fy_info["date_from"], date_to=fy_info["date_to"]
            )
        return fy_info

    def _compute_depreciation_table(self):
        table = []
        if (
            self.method_time in ["year", "number"]
            and not self.method_number
            and not self.method_end
        ):
            return table
        asset_date_start = self.date_start
        depreciation_start_date = self._get_depreciation_start_date(
            self._get_fy_info(asset_date_start)["record"]
        )
        depreciation_stop_date = self._get_depreciation_stop_date(
            depreciation_start_date
        )
        fy_date_start = asset_date_start
        while fy_date_start <= depreciation_stop_date:
            fy_info = self._get_fy_info(fy_date_start)
            table.append(
                {
                    "fy": fy_info["record"],
                    "date_start": fy_info["date_from"],
                    "date_stop": fy_info["date_to"],
                }
            )
            fy_date_start = fy_info["date_to"] + relativedelta(days=1)
        # Step 1:
        # Calculate depreciation amount per fiscal year.
        # This is calculation is skipped for method_time != 'year'.
        line_dates = self._compute_line_dates(
            table, depreciation_start_date, depreciation_stop_date
        )
        table = self._compute_depreciation_amount_per_fiscal_year(
            table, line_dates, depreciation_start_date, depreciation_stop_date
        )
        # Step 2:
        # Spread depreciation amount per fiscal year
        # over the depreciation periods.
        self._compute_depreciation_table_lines(
            table, depreciation_start_date, depreciation_stop_date, line_dates
        )

        return table

    def _get_depreciation_entry_name(self, seq):
        """ use this method to customise the name of the accounting entry """
        return (self.code or str(self.id)) + "/" + str(seq)

    def _compute_entries(self, date_end, check_triggers=False):
        # TODO : add ir_cron job calling this method to
        # generate periodical accounting entries
        result = []
        error_log = ""
        if check_triggers:
            recompute_obj = self.env["account.asset.recompute.trigger"]
            recomputes = recompute_obj.sudo().search([("state", "=", "open")])
            if recomputes:
                trigger_companies = recomputes.mapped("company_id")
                for asset in self:
                    if asset.company_id.id in trigger_companies.ids:
                        asset.compute_depreciation_board()

        depreciations = self.env["account.asset.line"].search(
            [
                ("asset_id", "in", self.ids),
                ("type", "=", "depreciate"),
                ("init_entry", "=", False),
                ("line_date", "<=", date_end),
                ("move_check", "=", False),
            ],
            order="line_date",
        )
        for depreciation in depreciations:
            try:
                with self.env.cr.savepoint():
                    result += depreciation.create_move()
            except Exception:
                e = exc_info()[0]
                tb = "".join(format_exception(*exc_info()))
                asset_ref = depreciation.asset_id.name
                if depreciation.asset_id.code:
                    asset_ref = "[{}] {}".format(depreciation.asset_id.code, asset_ref)
                error_log += _("\nError while processing asset '%s': %s") % (
                    asset_ref,
                    str(e),
                )
                error_msg = _("Error while processing asset '%s': \n\n%s") % (
                    asset_ref,
                    tb,
                )
                _logger.error("%s, %s", self._name, error_msg)

        if check_triggers and recomputes:
            companies = recomputes.mapped("company_id")
            triggers = recomputes.filtered(lambda r: r.company_id.id in companies.ids)
            if triggers:
                recompute_vals = {
                    "date_completed": fields.Datetime.now(),
                    "state": "done",
                }
                triggers.sudo().write(recompute_vals)

        return (result, error_log)

    @api.model
    def _xls_acquisition_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            "account",
            "name",
            "code",
            "date_start",
            "purchase_value",
            "depreciation_base",
            "salvage_value",
        ]

    @api.model
    def _xls_active_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            "account",
            "name",
            "code",
            "date_start",
            "purchase_value",
            "depreciation_base",
            "salvage_value",
            "period_start_value",
            "period_depr",
            "period_end_value",
            "period_end_depr",
            "method",
            "method_number",
            "prorata",
            "state",
        ]

    @api.model
    def _xls_removal_fields(self):
        """
        Update list in custom module to add/drop columns or change order
        """
        return [
            "account",
            "name",
            "code",
            "date_remove",
            "purchase_value",
            "depreciation_base",
            "salvage_value",
        ]

    @api.model
    def _xls_asset_template(self):
        """
        Template updates

        """
        return {}

    @api.model
    def _xls_acquisition_template(self):
        """
        Template updates

        """
        return {}

    @api.model
    def _xls_active_template(self):
        """
        Template updates

        """
        return {}

    @api.model
    def _xls_removal_template(self):
        """
        Template updates

        """
        return {}
