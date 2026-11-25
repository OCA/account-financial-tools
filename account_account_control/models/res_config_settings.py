# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import UserError

from .account_account import (
    CHECK_ACCOUNT_NAME_UNIQUE_PARAM,
    LOCK_USED_ACCOUNT_CODE_PARAM,
    REQUIRE_MODIFICATION_REASON_PARAM,
)


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    lock_used_account_code = fields.Boolean(
        string="Lock code of used accounts",
        config_parameter=LOCK_USED_ACCOUNT_CODE_PARAM,
    )
    check_account_name_unique = fields.Boolean(
        string="Check account label uniqueness",
        config_parameter=CHECK_ACCOUNT_NAME_UNIQUE_PARAM,
    )
    require_account_modification_reason = fields.Boolean(
        string="Require a modification reason",
        config_parameter=REQUIRE_MODIFICATION_REASON_PARAM,
    )

    def set_values(self):
        Account = self.env["account.account"]
        if (
            self.check_account_name_unique
            and not Account._is_account_name_unique_check_enabled()
        ):
            duplicates = Account._get_duplicate_name_accounts()
            if duplicates:
                raise UserError(
                    self.env._(
                        "The account label uniqueness cannot be checked as the "
                        "following accounts have the same label:\n%(accounts)s",
                        accounts="\n".join(
                            duplicates.sorted("name").mapped("display_name")
                        ),
                    )
                )
        return super().set_values()
