from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    writeoff_threshold_amount = fields.Monetary(
        string="Write-off Threshold",
        currency_field="currency_id",
        default=10.0,
        help="Residual balances below this amount will be written off automatically.",
    )
    writeoff_income_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Write-off Income Account",
        domain="[('deprecated', '=', False)]",
        help="Account credited when writing off a customer invoice residual.",
    )
    writeoff_expense_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Write-off Expense Account",
        domain="[('deprecated', '=', False)]",
        help="Account debited when writing off a vendor bill residual.",
    )
    writeoff_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Write-off Journal",
        domain="[('type', '=', 'general')]",
        help="Journal used to post write-off journal entries.",
    )
    writeoff_batch_size = fields.Integer(
        string="Write-off Batch Size",
        default=50,
        help=(
            "Number of invoices processed per background job when using the "
            "job queue companion module. Has no effect without that module."
        ),
    )
