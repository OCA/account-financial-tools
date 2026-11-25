# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import str2bool

LOCK_USED_ACCOUNT_CODE_PARAM = "account_account_control.lock_used_account_code"
CHECK_ACCOUNT_NAME_UNIQUE_PARAM = "account_account_control.check_account_name_unique"
REQUIRE_MODIFICATION_REASON_PARAM = (
    "account_account_control.require_modification_reason"
)


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_used_in_posted_move = fields.Boolean(
        compute="_compute_is_used_in_posted_move",
        help="Technical field: the account is used on at least one journal item "
        "of a posted journal entry.",
    )
    is_code_locked = fields.Boolean(compute="_compute_is_code_locked")
    is_modification_reason_required = fields.Boolean(
        compute="_compute_is_modification_reason_required"
    )
    modification_reason_id = fields.Many2one(
        comodel_name="account.account.modification.reason",
        string="Last Modification Reason",
        readonly=True,
        copy=False,
        ondelete="restrict",
        tracking=True,
    )

    def _compute_is_used_in_posted_move(self):
        used_ids = set(self._origin._get_used_in_posted_moves().ids)
        for account in self:
            account.is_used_in_posted_move = account._origin.id in used_ids

    @api.depends("is_used_in_posted_move")
    def _compute_is_code_locked(self):
        enabled = self._is_used_account_code_lock_enabled()
        for account in self:
            account.is_code_locked = enabled and account.is_used_in_posted_move

    def _compute_is_modification_reason_required(self):
        self.is_modification_reason_required = (
            self._is_modification_reason_required_enabled()
        )

    def _get_used_in_posted_moves(self):
        """Return the accounts of self used on journal items of posted entries"""
        if not self.ids:
            return self.browse()
        groups = (
            self.env["account.move.line"]
            .sudo()
            ._read_group(
                [("account_id", "in", self.ids), ("parent_state", "=", "posted")],
                groupby=["account_id"],
            )
        )
        return self.browse([account.id for (account,) in groups])

    @api.model
    def _is_used_account_code_lock_enabled(self):
        return str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(LOCK_USED_ACCOUNT_CODE_PARAM, "False")
        )

    @api.model
    def _is_modification_reason_required_enabled(self):
        return str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(REQUIRE_MODIFICATION_REASON_PARAM, "False")
        )

    @api.model
    def _is_account_name_unique_check_enabled(self):
        return str2bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(CHECK_ACCOUNT_NAME_UNIQUE_PARAM, "False")
        )

    @api.constrains("name", "company_ids")
    def _check_account_name_unique(self):
        if not self._is_account_name_unique_check_enabled():
            return
        for account in self.sudo():
            duplicate = account.search(
                [
                    ("id", "!=", account.id),
                    ("name", "=ilike", account.name),
                    ("company_ids", "in", account.company_ids.ids),
                ],
                limit=1,
            )
            if duplicate:
                raise ValidationError(
                    _(
                        "The label '%(name)s' is already used by the account "
                        "%(account)s.",
                        name=account.name,
                        account=duplicate.display_name,
                    )
                )

    @api.model
    def _get_duplicate_name_accounts(self):
        """Return the accounts sharing their label with another account of
        one of their companies"""
        accounts_by_key = defaultdict(lambda: self.browse())
        for account in self.sudo().search([]):  # pylint: disable=no-search-all
            for company in account.company_ids:
                accounts_by_key[(company, account.name.lower())] |= account
        duplicates = self.browse()
        for accounts in accounts_by_key.values():
            if len(accounts) > 1:
                duplicates |= accounts
        return duplicates

    @api.model_create_multi
    def create(self, vals_list):
        # The creation of an account writes on it (e.g. its code per company
        # from its code mapping): no modification reason is required for that
        accounts = super(
            AccountAccount, self.with_context(skip_account_modification_reason=True)
        ).create(vals_list)
        return accounts.with_env(self.env)

    def write(self, vals):
        # The code can be written directly or, per company, through its
        # company dependent storage (e.g. from the code mapping of the account)
        code_fnames = {"code", "code_store"} & vals.keys()
        if code_fnames and self._is_used_account_code_lock_enabled():
            self._check_used_account_code_change(code_fnames.pop(), vals)
        if (
            self._is_modification_reason_required_enabled()
            and not self._is_modification_reason_skipped()
        ):
            # Unchanged values are not tracked: reset the reason of the accounts
            # modified again for the same reason so that it is logged anyway
            same_reason_accounts = self._check_modification_reason(vals)
            if same_reason_accounts:
                super(
                    AccountAccount, same_reason_accounts.with_context(mail_notrack=True)
                ).write({"modification_reason_id": False})
        return super().write(vals)

    def _check_used_account_code_change(self, fname, vals):
        new_code = vals[fname] or False
        changed = self.filtered(lambda account: (account[fname] or False) != new_code)
        locked = changed._get_used_in_posted_moves()
        if locked:
            raise UserError(
                _(
                    "You cannot change the code of the following accounts as they "
                    "are used in posted journal entries:\n%(accounts)s",
                    accounts="\n".join(locked.mapped("display_name")),
                )
            )

    def _is_modification_reason_skipped(self):
        """No modification reason is required for technical updates"""
        context = self.env.context
        return (
            self.env.su
            or context.get("skip_account_modification_reason")
            # Loading of module data and of charts of accounts
            or context.get("install_mode")
            or context.get("chart_template_load")
        )

    def _check_modification_reason(self, vals):
        """Check the modification reason is given if needed and return the
        accounts already having this reason"""
        if not self or not vals.keys() - self._get_modification_reason_exempt_fields():
            return self.browse()
        reason = self.env["account.account.modification.reason"].browse(
            vals.get("modification_reason_id")
        )
        if not reason:
            raise UserError(
                _(
                    "A modification reason is required to modify the following "
                    "accounts:\n%(accounts)s",
                    accounts="\n".join(self.mapped("display_name")),
                )
            )
        return self.filtered(lambda account: account.modification_reason_id == reason)

    def _get_modification_reason_exempt_fields(self):
        """Fields that can be written without modification reason"""
        return set(self.env["mail.thread"]._fields) | {"modification_reason_id"}
