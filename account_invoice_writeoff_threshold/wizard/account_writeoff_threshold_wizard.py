from odoo import api, fields, models


class AccountWriteoffThresholdWizard(models.TransientModel):
    _name = "account.writeoff.threshold.wizard"
    _description = "Write-off Threshold Wizard"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    writeoff_date = fields.Date(
        string="Write-off Date",
        required=True,
        default=fields.Date.today,
        help="Date that will be used for the write-off journal entries.",
    )
    date_from = fields.Date(
        string="Invoice Date From",
        help="Filter: only consider moves with date on or after this date.",
    )
    date_to = fields.Date(
        string="Invoice Date To",
        help="Filter: only consider moves with date on or before this date.",
    )
    threshold_amount = fields.Monetary(
        related="company_id.writeoff_threshold_amount",
        readonly=True,
        string="Threshold",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
    )
    preview_line_ids = fields.One2many(
        comodel_name="account.writeoff.threshold.wizard.line",
        inverse_name="wizard_id",
        string="Moves to Write Off",
        readonly=False,
    )
    total_lines = fields.Integer(compute="_compute_totals")
    total_amount = fields.Monetary(
        compute="_compute_totals",
        currency_field="currency_id",
    )

    @api.depends("preview_line_ids.amount_residual", "preview_line_ids.skip")
    def _compute_totals(self):
        for rec in self:
            active = rec.preview_line_ids.filtered(lambda line: not line.skip)
            rec.total_lines = len(active)
            rec.total_amount = sum(active.mapped("amount_residual"))

    def action_preview(self):
        """Populate preview_line_ids with candidate move lines."""
        self.ensure_one()
        log_model = self.env["account.writeoff.log"]
        candidates = log_model._get_candidate_lines(
            self.company_id,
            date_from=self.date_from,
            date_to=self.date_to,
        )
        self.preview_line_ids = [(5, 0, 0)]
        lines = [
            {
                "wizard_id": self.id,
                "move_line_id": ml.id,
                "invoice_id": ml.move_id.id,
                "partner_id": ml.partner_id.id,
                "amount_residual": abs(ml.amount_residual),
            }
            for ml in candidates
        ]
        if lines:
            self.env["account.writeoff.threshold.wizard.line"].create(lines)
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_confirm(self):
        """Execute write-off on non-skipped preview lines and open the log."""
        self.ensure_one()
        log_model = self.env["account.writeoff.log"]
        company = self.company_id
        log_model._check_writeoff_config(company)

        active_lines = self.preview_line_ids.filtered(lambda line: not line.skip)
        move_line_ids = active_lines.mapped("move_line_id").ids

        log = log_model.create(
            {
                "threshold_amount": company.writeoff_threshold_amount,
                "company_id": company.id,
                "state": "draft",
                "writeoff_date": self.writeoff_date,
                "date_from": self.date_from,
                "date_to": self.date_to,
            }
        )
        candidates = self.env["account.move.line"].browse(move_line_ids)
        log_model._dispatch_writeoff(log, candidates, writeoff_date=self.writeoff_date)

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.writeoff.log",
            "res_id": log.id,
            "view_mode": "form",
        }


class AccountWriteoffThresholdWizardLine(models.TransientModel):
    _name = "account.writeoff.threshold.wizard.line"
    _description = "Write-off Threshold Wizard Preview Line"

    wizard_id = fields.Many2one(
        comodel_name="account.writeoff.threshold.wizard",
        ondelete="cascade",
    )
    skip = fields.Boolean(
        default=False,
        help="Check to exclude this line from the write-off.",
    )
    move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Move Line",
        readonly=True,
    )
    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Move",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        readonly=True,
    )
    move_type = fields.Selection(
        related="invoice_id.move_type",
        readonly=True,
    )
    amount_residual = fields.Monetary(
        string="Residual Amount",
        readonly=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="wizard_id.currency_id",
        readonly=True,
    )
