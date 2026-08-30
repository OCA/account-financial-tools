from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    writeoff_threshold_amount = fields.Monetary(
        related="company_id.writeoff_threshold_amount",
        readonly=False,
    )
    writeoff_income_account_id = fields.Many2one(
        related="company_id.writeoff_income_account_id",
        readonly=False,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
    )
    writeoff_expense_account_id = fields.Many2one(
        related="company_id.writeoff_expense_account_id",
        readonly=False,
        domain="[('deprecated', '=', False), ('company_id', '=', company_id)]",
    )
    writeoff_journal_id = fields.Many2one(
        related="company_id.writeoff_journal_id",
        readonly=False,
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]",
    )
    writeoff_batch_size = fields.Integer(
        related="company_id.writeoff_batch_size",
        readonly=False,
    )
