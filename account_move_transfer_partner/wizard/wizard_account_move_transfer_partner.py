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
                    invoice = move._origin
                else:
                    invoice = move
                total_amount_due += invoice.currency_id.with_context(
                    date=self.account_date or fields.Date.today()
                ).compute(invoice.amount_residual, self.currency_id)
            self.total_amount_due = total_amount_due
            self.amount_to_transfer = self.total_amount_due

    @api.model
    def default_get(self, fields_list):
        values = super(WizardAccountMoveTransferPartner, self).default_get(fields_list)
        moves = (
            self.env["account.move"]
            .browse(self.env.context.get("active_ids"))
            .filtered(lambda x: x.state == "posted")
        )
        values["origin_partner_ids"] = moves.mapped("partner_id").ids
        values["move_ids"] = moves.filtered(lambda x: x.is_invoice()).ids
        values["no_invoice_documents"] = (
            len(moves.filtered(lambda x: not x.is_invoice())) >= 1
        )
        due_amount = abs(sum(moves.mapped("amount_residual")))
        values["total_amount_due"] = due_amount
        values["amount_to_transfer"] = due_amount
        values["allow_edit_amount_to_transfer"] = len(moves) == 1
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
                credit_line_data.update(
                    {
                        "partner_id": move.is_inbound()
                        and move.partner_id.id
                        or move.is_outbound()
                        and self.destination_partner_id.id,
                        "credit": amount,
                        "debit": 0.0,
                        "amount_currency": -amount_currency,
                        "date_maturity": line.date_maturity,
                    }
                )
                debit_line_data.update(
                    {
                        "partner_id": move.is_inbound()
                        and self.destination_partner_id.id
                        or move.is_outbound()
                        and move.partner_id.id,
                        "credit": 0.0,
                        "debit": amount,
                        "amount_currency": amount_currency,
                        "date_maturity": line.date_maturity,
                    }
                )
                credit_aml += aml_model.create(credit_line_data)
                debit_aml += aml_model.create(debit_line_data)
            new_move.action_post()
            if move.is_inbound():
                for aml in credit_aml:
                    move.js_assign_outstanding_line(aml.id)
            if move.is_outbound():
                for aml in debit_aml:
                    move.js_assign_outstanding_line(aml.id)
            new_moves |= new_move
        action = self.env.ref("account.action_move_journal_line").read()[0]
        action.update({"domain": [("id", "in", new_moves.ids)]})
        return action
