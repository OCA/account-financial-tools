# Copyright 2026 - TODAY, Marcel Savegnago <marcel.savegnago@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date

_logger = logging.getLogger(__name__)


class AccountAccount(models.Model):
    _inherit = "account.account"

    deactivation_date = fields.Date(
        tracking=True,
        copy=False,
        help="From this date on, journal entries can no longer use the "
        "account and, once the date is reached, the account is deprecated. "
        "Entries dated before it remain valid.",
    )

    @api.model
    def _is_deactivation_date_reached(self, deactivation_date):
        deactivation_date = fields.Date.to_date(deactivation_date)
        return bool(deactivation_date) and (
            deactivation_date <= fields.Date.context_today(self)
        )

    @api.model
    def _prepare_deactivation_vals(self, vals):
        """Let the date drive ``deprecated``. A bare flag keeps core behavior.

        Setting only ``deprecated`` must not invent a deactivation date.
        Accounts deprecated without a date stay blocked on every accounting
        date, which is what the rest of Accounting already expects.
        """
        if "deactivation_date" not in vals:
            return vals
        return dict(
            vals,
            deprecated=self._is_deactivation_date_reached(vals["deactivation_date"]),
        )

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(
            [self._prepare_deactivation_vals(vals) for vals in vals_list]
        )

    def write(self, vals):
        return super().write(self._prepare_deactivation_vals(vals))

    @api.onchange("deactivation_date")
    def _onchange_deactivation_date(self):
        for account in self:
            account.deprecated = self._is_deactivation_date_reached(
                account.deactivation_date
            )

    @api.constrains("deactivation_date")
    def _check_deactivation_date(self):
        accounts = self.filtered("deactivation_date")
        if not accounts:
            return
        taxed_accounts = (
            self.env["account.tax.repartition.line"]
            .sudo()
            .search([("account_id", "in", accounts.ids)])
            .account_id
        )
        if taxed_accounts:
            raise ValidationError(
                _(
                    "You cannot set a deactivation date on accounts used in a "
                    "tax distribution: %(accounts)s",
                    accounts=", ".join(taxed_accounts.mapped("display_name")),
                )
            )
        last_dates = dict(
            self.env["account.move.line"]
            .sudo()
            ._read_group(
                [
                    ("account_id", "in", accounts.ids),
                    ("parent_state", "=", "posted"),
                ],
                groupby=["account_id"],
                aggregates=["date:max"],
            )
        )
        for account in accounts:
            last_date = last_dates.get(account)
            if last_date and account.deactivation_date <= last_date:
                raise ValidationError(
                    _(
                        "The deactivation date of account %(account)s must be "
                        "later than %(date)s, the date of its last posted "
                        "journal item.",
                        account=account.display_name,
                        date=format_date(self.env, last_date),
                    )
                )

    @api.model
    def _cron_deprecate_due_accounts(self):
        accounts = self.search(
            [
                ("deactivation_date", "<=", fields.Date.context_today(self)),
                ("deprecated", "=", False),
            ]
        )
        for account in accounts:
            try:
                with self.env.cr.savepoint():
                    account.write({"deprecated": True})
            except UserError as error:
                _logger.warning(
                    "Could not deprecate account %s: %s", account.display_name, error
                )
                account.message_post(
                    body=_(
                        "The account could not be deprecated on its deactivation "
                        "date: %(error)s",
                        error=error.args[0],
                    )
                )
