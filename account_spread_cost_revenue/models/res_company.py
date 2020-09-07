# Copyright 2018-2020 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    default_spread_revenue_account_id = fields.Many2one(
        "account.account", string="Revenue Spread Account"
    )

    default_spread_expense_account_id = fields.Many2one(
        "account.account", string="Expense Spread Account"
    )

    default_spread_revenue_journal_id = fields.Many2one(
        "account.journal", string="Revenue Spread Journal"
    )

    default_spread_expense_journal_id = fields.Many2one(
        "account.journal", string="Expense Spread Journal"
    )

    allow_spread_planning = fields.Boolean(
        default=True,
        help="Disable this option if you do not want to allow the "
        "spreading before the invoice is validated.",
    )
    force_move_auto_post = fields.Boolean(
        "Auto-post spread lines",
        help="Enable this option if you want to post automatically the "
        "accounting moves of all the spreads.",
    )
    auto_archive_spread = fields.Boolean(
        "Auto-archive spread",
        help="Enable this option if you want the cron job to automatically "
        "archive the spreads when all lines are posted.",
    )
