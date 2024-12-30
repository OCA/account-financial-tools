# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import format_date

from odoo.addons.account.models.company import LOCK_DATE_FIELDS


class AccountUpdateLockDate(models.TransientModel):
    _name = "account.update.lock_date"
    _description = "Wizard to Update Accounting Lock Dates"

    company_id = fields.Many2one(comodel_name="res.company", required=True)
    fiscalyear_lock_date = fields.Date(
        string="Global Lock Date",
        help="Impossible to edit/create journal entries prior to and "
        "inclusive of this date. Subject to exceptions.",
    )
    tax_lock_date = fields.Date(
        string="Tax Return Lock Date",
        help="Impossible to edit/create journal entries related to a tax prior and "
        "inclusive of this date. Subject to exceptions.",
    )
    sale_lock_date = fields.Date(
        help="Impossible to edit/create sale journal entries prior to and "
        "inclusive of this date. Subject to exceptions.",
    )
    purchase_lock_date = fields.Date(
        help="Impossible to edit/create purchase journal entries prior to and "
        "inclusive of this date. Subject to exceptions.",
    )
    hard_lock_date = fields.Date(
        help="Impossible to edit/create journal entries prior to and "
        "inclusive of this date. This lock date is irreversible and "
        "does not allow any exception.",
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        company = self.env.company
        for lock_field in LOCK_DATE_FIELDS:
            res[lock_field] = company[lock_field]
        res["company_id"] = company.id
        return res

    def _check_execute_allowed(self):
        self.ensure_one()
        has_adviser_group = self.env.user.has_group("account.group_account_manager")
        if not (has_adviser_group or self.env.user._is_admin()):
            raise UserError(_("You are not allowed to execute this action."))

    def execute(self):
        self.ensure_one()
        self._check_execute_allowed()
        today = fields.Date.context_today(self)
        fields_sr = (
            self.env["ir.model.fields"]
            .sudo()
            .search_read(
                [("model", "=", self._name), ("name", "in", LOCK_DATE_FIELDS)],
                ["field_description", "name"],
            )
        )
        field2string = dict(
            (field["name"], field["field_description"]) for field in fields_sr
        )
        vals = {}
        for lock_field in LOCK_DATE_FIELDS:
            if self[lock_field] and self[lock_field] > today:
                raise UserError(
                    _(
                        "You tried to set %(field)s to %(date)s, "
                        "but it is in the future.",
                        field=field2string[lock_field],
                        date=format_date(self.env, self[lock_field]),
                    )
                )
            vals[lock_field] = self[lock_field]
        self.company_id.sudo().write(vals)
