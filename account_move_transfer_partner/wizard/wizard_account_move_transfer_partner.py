# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class WizardAccountMoveTransferPartner(models.TransientModel):

    _name = "wizard.account.move.transfer.partner"
    _description = "Wizard to transfer due amount to another partner"

    origin_partner_ids = fields.Many2many(
        comodel_name="res.partner", string="Origin Partner", readonly=True
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
    )
    move_ids = fields.Many2many(
        comodel_name="account.move", string="Moves Selected", readonly=True
    )
    destination_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Destination partner", required=True
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        required=True,
        domain=[("type", "=", "general")],
        default=lambda self: self.env["account.journal"]
        .search([("type", "=", "general")], limit=1)
        .id,
    )
    account_date = fields.Date(
        string="Account date", required=True, default=fields.Date.today()
    )
    total_amount_due = fields.Monetary(
        string="Total Amount Due",
        readonly=True,
        currency_field="currency_id",
    )
    allow_edit_amount_to_transfer = fields.Boolean(
        string="Allow edit amount to transfer?",
        readonly=True,
    )
    no_invoice_documents = fields.Boolean(string="No invoice documents?", readonly=True)
    amount_to_transfer = fields.Monetary(
        string="Amount to transfer",
        required=True,
        currency_field="currency_id",
    )

    @api.onchange("currency_id", "account_date")
    def _onchange_currency_id(self):
        if self.currency_id:
            total_amount_due = 0
            for move in self.move_ids:
                if move._origin:
                    real_move = move._origin
                else:
                    real_move = move
                total_amount_due += real_move.currency_id.with_context(
                    date=self.account_date or fields.Date.today()
                ).compute(real_move.amount_residual, self.currency_id)
                if real_move.payment_id:
                    (
                        liquidity_lines,
                        counterpart_lines,
                        writeoff_lines,
                    ) = real_move.payment_id._seek_for_lines()
                    payment_amount_due = abs(
                        sum(counterpart_lines.mapped("amount_residual"))
                    )
                    total_amount_due += real_move.payment_id.currency_id.with_context(
                        date=self.account_date or fields.Date.today()
                    ).compute(payment_amount_due, self.currency_id)
            self.total_amount_due = total_amount_due
            self.amount_to_transfer = self.total_amount_due

    @api.model
    def default_get(self, fields_list):
        values = super(WizardAccountMoveTransferPartner, self).default_get(fields_list)
        current_model = self.env.context.get("active_model")
        moves = self.env["account.move"].browse()
        records = self.env[current_model].browse(self.env.context.get("active_ids"))
        if current_model == "account.payment":
            moves = records.mapped("move_id")
        elif current_model == "account.move":
            moves = records
        moves = moves.filtered(lambda x: x.state == "posted")
        allowed_moves = moves.filtered(lambda x: x.is_invoice() or x.payment_id)
        values["origin_partner_ids"] = moves.mapped("partner_id").ids
        values["move_ids"] = allowed_moves.ids
        values["no_invoice_documents"] = len(moves - allowed_moves) >= 1
        due_amount = abs(sum(allowed_moves.mapped("amount_residual")))
        for payment in allowed_moves.mapped("payment_id"):
            (
                liquidity_lines,
                counterpart_lines,
                writeoff_lines,
            ) = payment._seek_for_lines()
            due_amount += abs(sum(counterpart_lines.mapped("amount_residual")))
        values["total_amount_due"] = due_amount
        values["amount_to_transfer"] = due_amount
        values["allow_edit_amount_to_transfer"] = len(allowed_moves) == 1
        return values

    def action_create_move(self):
        am_model = self.env["account.move"]
        aml_model = self.env["account.move.line"].with_context(
            check_move_validity=False
        )
        if self.amount_to_transfer <= 0:
            raise ValidationError(_("Amount to transfer should be bigger than zero"))
        if (
            float_compare(
                self.amount_to_transfer,
                self.total_amount_due,
                precision_rounding=self.env.company.currency_id.rounding or 0.01,
            )
            == 1
        ):
            raise ValidationError(
                _(
                    "Amount to transfer %s should be equal or lower than total amount due %s"
                )
                % (self.amount_to_transfer, self.total_amount_due)
            )
        new_moves = am_model.browse()
        for move in self.move_ids:
            new_move = am_model.create(
                {
                    "date": self.account_date,
                    "journal_id": self.journal_id.id,
                    "ref": _("Transfer amount due from %s") % (move.display_name),
                    "state": "draft",
                    "move_type": "entry",
                }
            )
            reconcilable_account = move.line_ids.mapped("account_id").filtered(
                lambda x: x.user_type_id.type in ("receivable", "payable")
            )
            if move.payment_id:
                (
                    liquidity_lines,
                    counterpart_lines,
                    writeoff_lines,
                ) = move.payment_id._seek_for_lines()
                lines = counterpart_lines.filtered(lambda x: not x.reconciled)
            else:
                lines = move.line_ids.filtered(
                    lambda line: line.account_id == reconcilable_account
                    and not line.reconciled
                )
            common_data = {
                "account_id": reconcilable_account.id,
                "move_id": new_move.id,
                "currency_id": self.currency_id.id,
                "ref": _("Transfer due amount from %s") % move.display_name,
            }
            amount_to_apply = (
                self.allow_edit_amount_to_transfer
                and self.amount_to_transfer
                or move.amount_residual
            )
            credit_aml = aml_model.browse()
            debit_aml = aml_model.browse()
            for line in lines:
                amount = min(amount_to_apply, abs(line.amount_residual))
                amount_to_apply -= amount
                amount_currency = (
                    move.currency_id.id != self.currency_id.id and amount or 0.0
                )
                amount = self.currency_id.with_context(date=self.account_date).compute(
                    amount, move.currency_id
                )
                credit_line_data = common_data.copy()
                debit_line_data = common_data.copy()
                is_inbound = (
                    move.is_inbound() or move.payment_id.partner_type == "supplier"
                )
                is_outbound = (
                    move.is_outbound() or move.payment_id.partner_type == "customer"
                )
                partner = line.move_id.payment_id.partner_id or line.move_id.partner_id
                credit_line_data.update(
                    {
                        "partner_id": is_inbound
                        and partner.id
                        or is_outbound
                        and self.destination_partner_id.id,
                        "credit": amount,
                        "debit": 0.0,
                        "amount_currency": -amount_currency,
                        "date_maturity": line.date_maturity,
                    }
                )
                debit_line_data.update(
                    {
                        "partner_id": is_inbound
                        and self.destination_partner_id.id
                        or is_outbound
                        and partner.id,
                        "credit": 0.0,
                        "debit": amount,
                        "amount_currency": amount_currency,
                        "date_maturity": line.date_maturity,
                    }
                )
                credit_aml += aml_model.create(credit_line_data)
                debit_aml += aml_model.create(debit_line_data)
            new_move.action_post()
            if is_inbound:
                if move.payment_id:
                    lines_not_reconciled = lines.filtered(lambda x: not x.reconciled)
                    lines_not_reconciled |= credit_aml
                    lines_not_reconciled.reconcile()
                else:
                    for aml in credit_aml:
                        move.js_assign_outstanding_line(aml.id)
            if is_outbound:
                if move.payment_id:
                    lines_not_reconciled = lines.filtered(lambda x: not x.reconciled)
                    lines_not_reconciled |= debit_aml
                    lines_not_reconciled.reconcile()
                else:
                    for aml in debit_aml:
                        move.js_assign_outstanding_line(aml.id)
            new_moves |= new_move
        action = self.env.ref("account.action_move_journal_line").read()[0]
        action.update({"domain": [("id", "in", new_moves.ids)]})
        return action
