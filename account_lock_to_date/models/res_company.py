# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

SOFT_LOCK_TO_DATE_FIELDS = [
    "fiscalyear_lock_to_date",
    "sale_lock_to_date",
    "purchase_lock_to_date",
]

LOCK_TO_DATE_FIELDS = [
    *SOFT_LOCK_TO_DATE_FIELDS,
    "hard_lock_to_date",
]


class ResCompany(models.Model):
    _inherit = "res.company"

    sale_lock_to_date = fields.Date(
        string="Sales Lock To Date",
        tracking=True,
        help="Prevents creation and modification of entries in sales journals"
        " posterior to the defined date inclusive.",
    )
    purchase_lock_to_date = fields.Date(
        tracking=True,
        help="Prevents creation and modification of entries in purchase journals"
        " posterior to the defined date inclusive.",
    )
    fiscalyear_lock_to_date = fields.Date(
        string="Global Lock To Date",
        tracking=True,
        help="No users can edit accounts posterior to this date."
        " Use it for fiscal year locking for example.",
    )
    hard_lock_to_date = fields.Date(
        tracking=True,
        help='Like the "Global Lock Date", but no exceptions are possible.',
    )

    user_fiscalyear_lock_to_date = fields.Date(
        compute="_compute_user_fiscalyear_lock_to_date"
    )
    user_sale_lock_to_date = fields.Date(compute="_compute_user_sale_lock_to_date")
    user_purchase_lock_to_date = fields.Date(
        compute="_compute_user_purchase_lock_to_date"
    )
    user_hard_lock_to_date = fields.Date(compute="_compute_user_hard_lock_to_date")

    @api.depends("fiscalyear_lock_to_date")
    @api.depends_context("uid", "ignore_exceptions")
    def _compute_user_fiscalyear_lock_to_date(self):
        ignore_exceptions = bool(self.env.context.get("ignore_exceptions", False))
        for company in self:
            company.user_fiscalyear_lock_to_date = company._get_user_lock_to_date(
                "fiscalyear_lock_to_date", ignore_exceptions
            )

    @api.depends("sale_lock_to_date")
    @api.depends_context("uid", "ignore_exceptions")
    def _compute_user_sale_lock_to_date(self):
        ignore_exceptions = bool(self.env.context.get("ignore_exceptions", False))
        for company in self:
            company.user_sale_lock_to_date = company._get_user_lock_to_date(
                "sale_lock_to_date", ignore_exceptions
            )

    @api.depends("purchase_lock_to_date")
    @api.depends_context("uid", "ignore_exceptions")
    def _compute_user_purchase_lock_to_date(self):
        ignore_exceptions = bool(self.env.context.get("ignore_exceptions", False))
        for company in self:
            company.user_purchase_lock_to_date = company._get_user_lock_to_date(
                "purchase_lock_to_date", ignore_exceptions
            )

    @api.depends("hard_lock_to_date")
    def _compute_user_hard_lock_to_date(self):
        for company in self:
            company.user_hard_lock_to_date = (
                min(
                    c.hard_lock_to_date
                    for c in company.with_context(active_test=False).sudo().parent_ids
                    if c.hard_lock_to_date
                )
                if any(
                    c.hard_lock_to_date
                    for c in company.with_context(active_test=False).sudo().parent_ids
                )
                else False
            )

    def _validate_locks(self, values):
        res = super()._validate_locks(values)
        if "hard_lock_to_date" in values:
            hard_lock_to_date = fields.Date.to_date(values["hard_lock_to_date"])
            for company in self:
                if not company.hard_lock_to_date:
                    continue
                if not hard_lock_to_date:
                    raise ValidationError(_("The Hard Lock Date cannot be removed."))
                if hard_lock_to_date > company.hard_lock_to_date:
                    raise ValidationError(
                        _(
                            "A new Hard Lock To Date must be prior "
                            "(or equal) to the previous one."
                        )
                    )
            nb_draft_entries = self.env["account.move"].search(
                [
                    ("company_id", "child_of", self.ids),
                    ("state", "=", "draft"),
                    ("date", ">=", hard_lock_to_date),
                ],
                limit=1,
            )
            if nb_draft_entries:
                raise ValidationError(
                    _(
                        "There are still unposted entries in the period to date"
                        " you want to hard lock. "
                        "You should either post or delete them."
                    )
                )
        self.env["res.company"].invalidate_model(
            fnames=[f"user_{field}" for field in LOCK_TO_DATE_FIELDS if field in values]
        )
        return res

    def _get_user_lock_to_date(self, soft_lock_to_date_field, ignore_exceptions=False):
        self.ensure_one()
        soft_lock_to_date = False
        # We need to use sudo, since we might not have access to a parent company.
        for company in self.sudo().parent_ids:
            if company[soft_lock_to_date_field]:
                if ignore_exceptions:
                    exception = None
                else:
                    exception = self.env["account.lock_exception"].search(
                        [
                            ("state", "=", "active"),  # checks the datetime
                            "|",
                            ("user_id", "=", None),
                            ("user_id", "=", self.env.user.id),
                            (
                                soft_lock_to_date_field,
                                ">",
                                company[soft_lock_to_date_field],
                            ),
                            ("company_id", "=", company.id),
                        ],
                        order="lock_date asc NULLS FIRST",
                        limit=1,
                    )
                if exception:
                    # The search domain of the exception ensures
                    # `exception[
                    #      soft_lock_to_date_field] > company[
                    #                                   soft_lock_to_date_field]`
                    # or `exception[soft_lock_to_date_field] is False`
                    soft_lock_to_date = (
                        min(soft_lock_to_date, exception[soft_lock_to_date_field])
                        if soft_lock_to_date and exception[soft_lock_to_date_field]
                        else soft_lock_to_date
                        or exception[soft_lock_to_date_field]
                        or False
                    )
                else:
                    soft_lock_to_date = (
                        min(soft_lock_to_date, company[soft_lock_to_date_field])
                        if soft_lock_to_date and company[soft_lock_to_date_field]
                        else soft_lock_to_date
                        or company[soft_lock_to_date_field]
                        or False
                    )
        return soft_lock_to_date

    def _get_user_fiscal_lock_to_date(self, journal, ignore_exceptions=False):
        self.ensure_one()
        company = self.with_context(ignore_exceptions=ignore_exceptions)
        lock = (
            min(company.user_fiscalyear_lock_to_date, company.user_hard_lock_to_date)
            if company.user_fiscalyear_lock_to_date and company.user_hard_lock_to_date
            else company.user_fiscalyear_lock_to_date
            or company.user_hard_lock_to_date
            or False
        )
        if journal.type == "sale":
            lock = (
                min(company.user_sale_lock_to_date, lock)
                if company.user_sale_lock_to_date and lock
                else company.user_sale_lock_to_date or lock or False
            )
        elif journal.type == "purchase":
            lock = (
                min(company.user_purchase_lock_to_date, lock)
                if company.user_purchase_lock_to_date and lock
                else company.user_purchase_lock_to_date or lock or False
            )
        return lock

    def _get_violated_soft_lock_to_date(self, soft_lock_to_date_field, date):
        violated_date = None
        if not self:
            return violated_date
        self.ensure_one()
        user_lock_to_date_field = f"user_{soft_lock_to_date_field}"
        regular_lock_to_date = self.with_context(ignore_exceptions=True)[
            user_lock_to_date_field
        ]
        if regular_lock_to_date and date >= regular_lock_to_date:
            user_lock_to_date = self.with_context(ignore_exceptions=False)[
                user_lock_to_date_field
            ]
            violated_date = (
                None
                if regular_lock_to_date and date < user_lock_to_date
                else user_lock_to_date
            )
        return violated_date

    def _get_lock_to_date_violations(
        self, accounting_date, fiscalyear=True, sale=True, purchase=True, hard=True
    ):
        self.ensure_one()
        locks = []
        if not accounting_date:
            return locks
        soft_lock_to_date_fields_to_check = [
            # (field, "to check")
            ("fiscalyear_lock_to_date", fiscalyear),
            ("sale_lock_to_date", sale),
            ("purchase_lock_to_date", purchase),
        ]
        for field, to_check in soft_lock_to_date_fields_to_check:
            if not to_check:
                continue
            violated_date = self._get_violated_soft_lock_to_date(field, accounting_date)
            if violated_date:
                locks.append((violated_date, field))
        if hard:
            hard_lock_date = self.user_hard_lock_to_date
            if hard_lock_date and accounting_date >= hard_lock_date:
                locks.append((hard_lock_date, "hard_lock_date"))
        return locks

    def write(self, values):
        companies = super().write(values)
        # We revoke all active exceptions affecting the changed lock to dates
        # and recreate them (with the updated lock to dates)
        changed_soft_lock_fields = [
            field for field in SOFT_LOCK_TO_DATE_FIELDS if field in values
        ]
        for company in self:
            active_exceptions = self.env["account.lock_exception"].search(
                self.env["account.lock_exception"]._get_active_exceptions_to_domain(
                    company, changed_soft_lock_fields
                ),
            )
            active_exceptions._recreate()
        return companies
