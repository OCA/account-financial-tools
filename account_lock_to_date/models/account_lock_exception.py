# Copyright 2025 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression

from .res_company import SOFT_LOCK_TO_DATE_FIELDS


class AccountLockException(models.Model):
    _inherit = "account.lock_exception"

    # The changed lock date
    lock_date_field = fields.Selection(
        selection_add=[
            ("fiscalyear_lock_to_date", "Global Lock To Date"),
            ("sale_lock_to_date", "Sales Lock To Date"),
            ("purchase_lock_to_date", "Purchase Lock To Date"),
        ],
        ondelete={
            "fiscalyear_lock_to_date": "cascade",
            "sale_lock_to_date": "cascade",
            "purchase_lock_to_date": "cascade",
        },
    )

    # (Non-stored) computed lock to date fields; c.f. res.company
    fiscalyear_lock_to_date = fields.Date(
        string="Global Lock To Date",
        compute="_compute_lock_dates",
        search="_search_fiscalyear_lock_to_date",
        help="The date the Global Lock To Date is set to by this exception. "
        "If the lock to date is not changed it is set to False.",
    )
    sale_lock_to_date = fields.Date(
        string="Sales Lock To Date",
        compute="_compute_lock_dates",
        search="_search_sale_lock_to_date",
        help="The date the Sale Lock To Date is set to by this exception. "
        "If the lock to date is not changed it is set to False.",
    )
    purchase_lock_to_date = fields.Date(
        compute="_compute_lock_dates",
        search="_search_purchase_lock_to_date",
        help="The date the Purchase Lock To Date is set to by this exception. "
        "If the lock to date is not changed it is set to False.",
    )

    @api.depends("lock_date_field", "lock_date")
    def _compute_lock_dates(self):
        res = super()._compute_lock_dates()
        for exception in self:
            for field in SOFT_LOCK_TO_DATE_FIELDS:
                if field == exception.lock_date_field:
                    exception[field] = exception.lock_date
                else:
                    exception[field] = False
        return res

    def _search_lock_to_date(self, field, operator, value):
        if operator not in [">", ">="] or not value:
            raise UserError(_("Operation not supported"))
        return [
            "&",
            ("lock_date_field", "=", field),
            "|",
            ("lock_date", "=", False),
            ("lock_date", operator, value),
        ]

    def _search_fiscalyear_lock_to_date(self, operator, value):
        return self._search_lock_to_date("fiscalyear_lock_to_date", operator, value)

    def _search_sale_lock_to_date(self, operator, value):
        return self._search_lock_to_date("sale_lock_to_date", operator, value)

    def _search_purchase_lock_to_date(self, operator, value):
        return self._search_lock_to_date("purchase_lock_to_date", operator, value)

    @api.model
    def _get_active_exceptions_to_domain(self, company, soft_lock_to_date_fields):
        return [
            *expression.OR(
                [(field, ">", company[field])]
                for field in soft_lock_to_date_fields
                if company[field]
            ),
            ("company_id", "=", company.id),
            ("state", "=", "active"),  # checks the datetime
        ]
