# Copyright 2025 Akretion France (https://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression
from odoo.tools import date_utils
from odoo.tools.misc import format_amount, format_date


class AccountDashboardBannerCell(models.Model):
    _name = "account.dashboard.banner.cell"
    _description = "Accounting Dashboard Banner Cell"
    _order = "sequence, id"

    sequence = fields.Integer()
    cell_type = fields.Selection(
        [
            ("income_fiscalyear", "Fiscal Year-to-date Income"),
            ("income_year", "Year-to-date Income"),
            ("income_quarter", "Quarter-to-date Income"),
            ("income_month", "Month-to-date Income"),
            ("liquidity", "Liquidity"),
            ("customer_debt", "Customer Debt"),
            ("customer_overdue", "Customer Overdue"),
            ("supplier_debt", "Supplier Debt"),
            # for lock dates, the key matches exactly the field name on res.company
            ("tax_lock_date", "Tax Return Lock Date"),
            ("sale_lock_date", "Sales Lock Date"),
            ("purchase_lock_date", "Purchase Lock Date"),
            ("fiscalyear_lock_date", "Global Lock Date"),
            ("hard_lock_date", "Hard Lock Date"),
        ],
        required=True,
    )
    custom_label = fields.Char()
    custom_tooltip = fields.Char()
    warn = fields.Boolean(string="Warning")
    warn_lock_date_days = fields.Integer(
        compute="_compute_warn_fields", store=True, readonly=False, precompute=True
    )
    warn_min = fields.Float(string="Minimum")
    warn_max = fields.Float(string="Maximum")
    warn_type_show = fields.Boolean(
        compute="_compute_warn_fields", store=True, precompute=True
    )
    warn_type = fields.Selection(
        [
            ("under", "Under Minimum"),
            ("above", "Above Maximum"),
            ("outside", "Under Minimum or Above Maximum"),
            ("inside", "Between Minimum and Maximum"),
        ],
        default="under",
    )

    _sql_constraints = [
        (
            "warn_lock_date_days_positive",
            "CHECK(warn_lock_date_days >= 0)",
            "Warn if lock date is older than N days must be positive or null.",
        )
    ]

    @api.constrains("warn_min", "warn_max", "warn_type", "warn", "cell_type")
    def _check_warn_config(self):
        for cell in self:
            if (
                cell.cell_type
                and not cell.cell_type.endswith("_lock_date")
                and cell.warn
                and cell.warn_type in ("outside", "inside")
                and cell.warn_max <= cell.warn_min
            ):
                cell_type2label = dict(
                    self.fields_get("cell_type", "selection")["cell_type"]["selection"]
                )
                raise ValidationError(
                    _(
                        "On cell '%(cell_type)s' with warning enabled, "
                        "the minimum (%(warn_min)s) must be under "
                        "the maximum (%(warn_max)s).",
                        cell_type=cell_type2label[cell.cell_type],
                        warn_min=cell.warn_min,
                        warn_max=cell.warn_max,
                    )
                )

    @api.model
    def _default_warn_lock_date_days(self, cell_type):
        defaultmap = {
            "tax_lock_date": 61,  # 2 months
            "sale_lock_date": 35,  # 1 month + a few days
            "purchase_lock_date": 61,
            "fiscalyear_lock_date": 61,  # 2 months
            "hard_lock_date": 520,  # FY final closing, 1 year + 5 months
        }
        return defaultmap.get(cell_type)

    @api.depends("cell_type", "warn")
    def _compute_warn_fields(self):
        for cell in self:
            warn_type_show = False
            warn_lock_date_days = 0
            if cell.cell_type and cell.warn:
                if cell.cell_type.endswith("_lock_date"):
                    warn_lock_date_days = self._default_warn_lock_date_days(
                        cell.cell_type
                    )
                else:
                    warn_type_show = True
            cell.warn_type_show = warn_type_show
            cell.warn_lock_date_days = warn_lock_date_days

    @api.model
    def get_banner_data(self):
        """This is the method called by the JS code that displays the banner"""
        company = self.env.company
        return self._prepare_banner_data(company)

    def _prepare_speedy(self, company):
        lock_date_fields = [
            "tax_lock_date",
            "sale_lock_date",
            "purchase_lock_date",
            "fiscalyear_lock_date",
            "hard_lock_date",
        ]
        speedy = {
            "cell_type2label": dict(
                self.fields_get("cell_type", "selection")["cell_type"]["selection"]
            ),
            "lock_date2help": dict(
                (key, value["help"])
                for (key, value) in company.fields_get(lock_date_fields, "help").items()
            ),
            "today": fields.Date.context_today(self),
        }
        return speedy

    @api.model
    def _prepare_banner_data(self, company):
        # The order in this list will be the display order in the banner
        # In fact, it's not a list but a dict. I tried to make it work by returning
        # a list but it seems OWL only accepts dicts (I always get errors on lists)
        cells = self.search([])
        speedy = cells._prepare_speedy(company)
        res = {}
        seq = 0
        for cell in cells:
            seq += 1
            cell_data = cell._prepare_cell_data(company, speedy)
            cell._update_cell_warn(cell_data)
            res[seq] = cell_data
        # from pprint import pprint
        # pprint(res)
        return res

    def _prepare_cell_data_liquidity(self, company, speedy):
        self.ensure_one()
        journals = self.env["account.journal"].search(
            [
                ("company_id", "=", company.id),
                ("type", "in", ("bank", "cash", "credit")),
                ("default_account_id", "!=", False),
            ]
        )
        accounts = journals.default_account_id
        return (accounts, 1, False, False)

    def _prepare_cell_data_supplier_debt(self, company, speedy):
        accounts = (
            self.env["res.partner"]
            ._fields["property_account_payable_id"]
            .get_company_dependent_fallback(self.env["res.partner"])
        )
        return (accounts, -1, False, False)

    def _prepare_cell_data_income(self, company, speedy):
        cell_type = self.cell_type
        accounts = self.env["account.account"].search(
            [
                ("company_ids", "in", [company.id]),
                ("account_type", "in", ("income", "income_other")),
            ]
        )
        if cell_type == "income_fiscalyear":
            start_date, end_date = date_utils.get_fiscal_year(
                speedy["today"],
                day=company.fiscalyear_last_day,
                month=int(company.fiscalyear_last_month),
            )
        elif cell_type == "income_month":
            start_date = speedy["today"] + relativedelta(day=1)
        elif cell_type == "income_year":
            start_date = speedy["today"] + relativedelta(day=1, month=1)
        elif cell_type == "income_quarter":
            month_start_quarter = 3 * ((speedy["today"].month - 1) // 3) + 1
            start_date = speedy["today"] + relativedelta(
                day=1, month=month_start_quarter
            )
        specific_domain = [("date", ">=", start_date)]
        specific_tooltip = _("from %s") % format_date(self.env, start_date)
        return (accounts, -1, specific_domain, specific_tooltip)

    def _prepare_cell_data_customer_debt(self, company, speedy):
        accounts = (
            self.env["res.partner"]
            ._fields["property_account_receivable_id"]
            .get_company_dependent_fallback(self.env["res.partner"])
        )
        if hasattr(company, "account_default_pos_receivable_account_id"):
            accounts |= company.account_default_pos_receivable_account_id
        return (accounts, 1, False, False)

    def _prepare_cell_data_customer_overdue(self, company, speedy):
        accounts, sign, specific_domain, specific_tooltip = (
            self._prepare_cell_data_customer_debt(company, speedy)
        )
        specific_domain = expression.OR(
            [
                [("date_maturity", "=", False)],
                [("date_maturity", "<", speedy["today"])],
                [
                    ("date_maturity", "=", speedy["today"]),
                    ("journal_id.type", "!=", "sale"),
                ],
            ]
        )
        specific_tooltip = _("with due date before %s") % format_date(
            self.env, speedy["today"]
        )
        return (accounts, sign, specific_domain, specific_tooltip)

    def _prepare_cell_data(self, company, speedy):
        """Inherit this method to change the computation of a cell type"""
        self.ensure_one()
        cell_type = self.cell_type
        value = raw_value = tooltip = warn = False
        if cell_type.endswith("lock_date"):
            raw_value = company[cell_type]
            value = raw_value and format_date(self.env, raw_value)
            tooltip = speedy["lock_date2help"][cell_type]
            if self.warn:
                if not raw_value:
                    warn = True
                elif raw_value < speedy["today"] - relativedelta(
                    days=self.warn_lock_date_days
                ):
                    warn = True
        else:
            accounts = False
            if hasattr(self, f"_prepare_cell_data_{cell_type}"):
                specific_method = getattr(self, f"_prepare_cell_data_{cell_type}")
                accounts, sign, specific_domain, specific_tooltip = specific_method(
                    company, speedy
                )
            elif cell_type.startswith("income_"):
                accounts, sign, specific_domain, specific_tooltip = (
                    self._prepare_cell_data_income(company, speedy)
                )
            if accounts:
                domain = (specific_domain or []) + [
                    ("company_id", "=", company.id),
                    ("account_id", "in", accounts.ids),
                    ("date", "<=", speedy["today"]),
                    ("parent_state", "=", "posted"),
                ]
                rg_res = self.env["account.move.line"]._read_group(
                    domain, aggregates=["balance:sum"]
                )
                assert sign in (1, -1)
                raw_value = rg_res and rg_res[0][0] * sign or 0
                value = format_amount(self.env, raw_value, company.currency_id)
                tooltip = _(
                    "Balance of account(s) %(account_codes)s%(specific)s.",
                    account_codes=", ".join(accounts.mapped("code")),
                    specific=specific_tooltip and f" {specific_tooltip}" or "",
                )
        res = {
            "cell_type": cell_type,
            "label": self.custom_label or speedy["cell_type2label"][cell_type],
            "raw_value": raw_value,
            "value": value or _("None"),
            "tooltip": self.custom_tooltip or tooltip,
            "warn": warn,
        }
        return res

    def _update_cell_warn(self, cell_data):
        self.ensure_one()
        if (
            not cell_data.get("warn")
            and self.warn
            and self.warn_type
            and isinstance(cell_data["raw_value"], (int | float))
        ):
            raw_value = cell_data["raw_value"]
            if (
                (self.warn_type == "under" and raw_value < self.warn_min)
                or (self.warn_type == "above" and raw_value > self.warn_max)
                or (
                    self.warn_type == "outside"
                    and (raw_value < self.warn_min or raw_value > self.warn_max)
                )
                or (
                    self.warn_type == "inside"
                    and raw_value > self.warn_min
                    and raw_value < self.warn_max
                )
            ):
                cell_data["warn"] = True

    @api.depends("cell_type", "custom_label")
    def _compute_display_name(self):
        type2name = dict(
            self.fields_get("cell_type", "selection")["cell_type"]["selection"]
        )
        for cell in self:
            display_name = "-"
            if cell.custom_label:
                display_name = cell.custom_label
            elif cell.cell_type:
                display_name = type2name[cell.cell_type]
            cell.display_name = display_name
