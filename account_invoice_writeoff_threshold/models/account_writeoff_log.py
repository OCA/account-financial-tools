from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountWriteoffLog(models.Model):
    _name = "account.writeoff.log"
    _description = "Write-off Threshold Execution Log"
    _order = "execution_date desc"

    name = fields.Char(
        string="Reference",
        required=True,
        readonly=True,
        default=lambda self: self.env["ir.sequence"].next_by_code(
            "account.writeoff.log"
        ),
    )
    execution_date = fields.Datetime(
        readonly=True,
        default=fields.Datetime.now,
    )
    writeoff_date = fields.Date(
        string="Write-off Date",
        readonly=True,
        help="Date used on the write-off journal entries.",
    )
    date_from = fields.Date(
        string="Invoice Date From",
        readonly=True,
        help="Only invoices with invoice date on or after this date were considered.",
    )
    date_to = fields.Date(
        string="Invoice Date To",
        readonly=True,
        help="Only invoices with invoice date on or before this date were considered.",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        readonly=True,
        default=lambda self: self.env.company,
    )
    threshold_amount = fields.Monetary(
        string="Threshold Used",
        readonly=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="company_id.currency_id",
        readonly=True,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Pending"),
            ("in_progress", "Processing"),
            ("done", "Done"),
            ("partial", "Partially Done"),
        ],
        readonly=True,
        default="draft",
        help=(
            "In synchronous execution the state moves directly from draft to done. "
            "When using the job queue companion, the state is set to 'in_progress' "
            "while jobs are running and updated to 'done' or 'partial' when all "
            "jobs finish."
        ),
    )
    line_ids = fields.One2many(
        comodel_name="account.writeoff.log.line",
        inverse_name="log_id",
        string="Written-off Entries",
        readonly=True,
    )
    total_lines = fields.Integer(
        compute="_compute_totals",
        store=True,
    )
    total_amount = fields.Monetary(
        string="Total Amount Written Off",
        compute="_compute_totals",
        store=True,
        currency_field="currency_id",
    )

    @api.depends("line_ids.amount")
    def _compute_totals(self):
        for rec in self:
            rec.total_lines = len(rec.line_ids)
            rec.total_amount = sum(rec.line_ids.mapped("amount"))

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    @api.model
    def run_writeoff(
        self,
        writeoff_date=None,
        date_from=None,
        date_to=None,
        company_id=None,
    ):
        """
        Entry point called by the wizard.

        Validates configuration, finds candidate move lines, creates the log
        header, and delegates execution to _dispatch_writeoff(). The companion
        module overrides only _dispatch_writeoff() to add async behaviour.

        :param writeoff_date: date for the write-off journal entries; defaults to today
        :param date_from: only consider invoices with invoice_date >= date_from
        :param date_to: only consider invoices with invoice_date <= date_to
        :param company_id: res.company record; defaults to self.env.company
        :return: account.writeoff.log record
        """
        company = company_id or self.env.company
        self._check_writeoff_config(company)

        writeoff_date = writeoff_date or fields.Date.today()
        candidates = self._get_candidate_lines(
            company, date_from=date_from, date_to=date_to
        )
        log = self.create(
            {
                "threshold_amount": company.writeoff_threshold_amount,
                "company_id": company.id,
                "state": "draft",
                "writeoff_date": writeoff_date,
                "date_from": date_from,
                "date_to": date_to,
            }
        )
        self._dispatch_writeoff(log, candidates, writeoff_date=writeoff_date)
        return log

    # -------------------------------------------------------------------------
    # Public action
    # -------------------------------------------------------------------------

    def action_view_writeoff_moves(self):
        """Open the write-off journal entries created by this log."""
        self.ensure_one()
        move_ids = self.line_ids.mapped("writeoff_move_id").ids
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("id", "in", move_ids)],
            "name": _("Write-off Journal Entries"),
        }

    # -------------------------------------------------------------------------
    # Extension hooks — override these in companion modules, not run_writeoff
    # -------------------------------------------------------------------------

    def _dispatch_writeoff(self, log, candidates, writeoff_date=None):
        """
        Decide how to process candidate move lines and update the log state.

        Base behaviour: process all candidates synchronously in a single call
        and mark the log as done immediately.

        The queue companion module overrides this method to split candidates
        into batches and enqueue one job per batch, setting the log state to
        'in_progress' until all jobs complete.

        :param log: account.writeoff.log record (already created)
        :param candidates: account.move.line recordset of lines to write off
        :param writeoff_date: date for the write-off journal entries
        """
        self._process_batch(log.id, candidates.ids, writeoff_date=writeoff_date)
        log.state = "done"

    @api.model
    def _process_batch(self, log_id, move_line_ids, writeoff_date=None):
        """
        Write off a list of move lines and append lines to the log.

        This method is designed to run inside its own database transaction
        when called from a queue job. In synchronous execution it runs inside
        the caller's transaction.

        :param log_id: int — id of the account.writeoff.log record
        :param move_line_ids: list of int — ids of account.move.line to process
        :param writeoff_date: date for the write-off journal entries
        """
        log = self.browse(log_id)
        company = log.company_id
        income_account = company.writeoff_income_account_id
        expense_account = company.writeoff_expense_account_id
        journal = company.writeoff_journal_id
        writeoff_date = writeoff_date or fields.Date.today()

        move_lines = self.env["account.move.line"].browse(move_line_ids)
        log_lines = []
        for move_line in move_lines:
            residual = abs(move_line.amount_residual)
            writeoff_move = self._create_writeoff_entry(
                move_line, income_account, expense_account, journal, writeoff_date
            )
            log_lines.append(
                {
                    "log_id": log.id,
                    "invoice_id": move_line.move_id.id,
                    "amount": residual,
                    "writeoff_move_id": writeoff_move.id,
                }
            )
        if log_lines:
            self.env["account.writeoff.log.line"].create(log_lines)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    @api.model
    def _check_writeoff_config(self, company):
        """
        Raise UserError if any required configuration field is missing.

        :param company: res.company record
        """
        missing = []
        if not company.writeoff_threshold_amount:
            missing.append(_("Write-off Threshold"))
        if not company.writeoff_income_account_id:
            missing.append(_("Write-off Income Account"))
        if not company.writeoff_expense_account_id:
            missing.append(_("Write-off Expense Account"))
        if not company.writeoff_journal_id:
            missing.append(_("Write-off Journal"))
        if missing:
            raise UserError(
                _(
                    "Write-off configuration is incomplete. "
                    "Please set the following in Settings: %s"
                )
                % ", ".join(missing)
            )

    @api.model
    def _get_candidate_lines(self, company, date_from=None, date_to=None):
        """
        Return unreconciled receivable/payable move lines on posted invoices
        whose absolute residual is greater than zero and below the threshold.

        :param company: res.company record
        :param date_from: optional lower bound on invoice_date (inclusive)
        :param date_to: optional upper bound on invoice_date (inclusive)
        :return: account.move.line recordset
        """
        threshold = company.writeoff_threshold_amount
        domain = [
            ("company_id", "=", company.id),
            (
                "account_id.account_type",
                "in",
                ["asset_receivable", "liability_payable"],
            ),
            ("reconciled", "=", False),
            ("move_id.state", "=", "posted"),
            ("amount_residual", "!=", 0),
        ]
        if date_from:
            domain.append(("move_id.invoice_date", ">=", date_from))
        if date_to:
            domain.append(("move_id.invoice_date", "<=", date_to))
        return (
            self.env["account.move.line"]
            .search(domain)
            .filtered(lambda line: 0 < abs(line.amount_residual) < threshold)
        )

    @api.model
    def _create_writeoff_entry(
        self, move_line, income_account, expense_account, journal, writeoff_date=None
    ):
        """
        Create and post a balancing journal entry for move_line's residual,
        then reconcile the counterpart line with the original move_line.

        Debit / credit logic
        --------------------
        Receivable (debit balance — customer owes us):
          DR  income_account      (residual)
          CR  receivable_account  (residual)

        Payable (credit balance — we owe vendor):
          DR  payable_account     (abs residual)
          CR  expense_account     (abs residual)

        :param move_line: account.move.line — the unreconciled open line
        :param income_account: account.account for customer-side write-offs
        :param expense_account: account.account for vendor-side write-offs
        :param journal: account.journal for the write-off entry
        :param writeoff_date: date for the journal entry; defaults to today
        :return: account.move — the posted write-off journal entry
        """
        residual = move_line.amount_residual
        is_receivable = move_line.account_id.account_type == "asset_receivable"
        writeoff_account = income_account if is_receivable else expense_account
        entry_date = writeoff_date or fields.Date.today()

        if residual > 0:
            counterpart_debit, counterpart_credit = 0.0, residual
            writeoff_debit, writeoff_credit = residual, 0.0
        else:
            abs_residual = abs(residual)
            counterpart_debit, counterpart_credit = abs_residual, 0.0
            writeoff_debit, writeoff_credit = 0.0, abs_residual

        ref = _("Write-off: %s") % move_line.move_id.name
        writeoff_move = self.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": entry_date,
                "ref": ref,
                "company_id": move_line.company_id.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": move_line.account_id.id,
                            "partner_id": move_line.partner_id.id,
                            "debit": counterpart_debit,
                            "credit": counterpart_credit,
                            "name": ref,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "account_id": writeoff_account.id,
                            "partner_id": move_line.partner_id.id,
                            "debit": writeoff_debit,
                            "credit": writeoff_credit,
                            "name": ref,
                        },
                    ),
                ],
            }
        )
        writeoff_move.action_post()

        counterpart_line = writeoff_move.line_ids.filtered(
            lambda line: line.account_id == move_line.account_id
        )
        (move_line | counterpart_line).reconcile()
        return writeoff_move


class AccountWriteoffLogLine(models.Model):
    _name = "account.writeoff.log.line"
    _description = "Write-off Threshold Log Line"

    log_id = fields.Many2one(
        comodel_name="account.writeoff.log",
        ondelete="cascade",
        required=True,
    )
    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Invoice / Bill",
        readonly=True,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        related="invoice_id.partner_id",
        readonly=True,
        store=True,
    )
    move_type = fields.Selection(
        related="invoice_id.move_type",
        readonly=True,
        store=True,
    )
    amount = fields.Monetary(
        string="Amount Written Off",
        readonly=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        related="log_id.currency_id",
        readonly=True,
    )
    writeoff_move_id = fields.Many2one(
        comodel_name="account.move",
        string="Write-off Entry",
        readonly=True,
    )
