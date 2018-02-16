# Copyright 2018 Eficent Business and IT Consulting Services S.L.
#   (http://www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models, _
from odoo.tools import float_is_zero
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AccountFxSpot(models.Model):
    _name = "account.fx.spot"
    _description = "Foreign Exchange Spot Transaction"
    _inherit = "mail.thread"
    _order = "date_transaction desc, name desc, id desc"

    name = fields.Char(
        string="Reference", index=True,
        readonly=True, copy=False,
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("done", "Done"),
            ("cancel", "Cancelled")],
        string="Status", index=True, readonly=True, default="draft",
    )
    date_transaction = fields.Date(
        string="Transaction Date",
        readonly=True, states={"draft": [("readonly", False)]}, index=True,
        default=fields.Date.today(),
        help="Keep empty to use the current date", copy=False,
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner", string="Partner", change_default=True,
        required=True, readonly=True, states={"draft": [("readonly", False)]},
        track_visibility="always",
    )
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', store=True,
        readonly=True,
        compute_sudo=True,
    )  # TODO: fix payment logic to usi this.
    in_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Incoming Currency",
        required=True, readonly=True, states={"draft": [("readonly", False)]},
    )
    amount_in = fields.Monetary(
        string="Received Amount",
        currency_field="in_currency_id",
        required=True, readonly=True, states={"draft": [("readonly", False)]},
    )
    residual_in = fields.Monetary(
        string="Remaining amount to receive",
        currency_field="in_currency_id",
        readonly=True,
        compute="_compute_residual", store=True,
    )
    residual_company_in = fields.Monetary(
        string="Remaining amount to receive in company currency",
        currency_field="company_currency_id",
        readonly=True,
        compute="_compute_residual", store=True,
    )
    out_currency_id = fields.Many2one(
        comodel_name="res.currency", string="Outgoing Currency",
        required=True, readonly=True, states={"draft": [("readonly", False)]},
    )
    amount_out = fields.Monetary(
        string="Issued Amount",
        currency_field="out_currency_id",
        required=True, readonly=True, states={"draft": [("readonly", False)]},
    )
    residual_out = fields.Monetary(
        string="Remaining amount due",
        currency_field="out_currency_id",
        readonly=True,
        compute="_compute_residual", store=True,
    )
    residual_company_out = fields.Monetary(
        string="Remaining amount due in company currency",
        currency_field="company_currency_id",
        readonly=True,
        compute="_compute_residual", store=True,
    )
    payment_ids = fields.Many2many(
        comodel_name="account.payment",
        relation="account_fx_spot_payment_rel",
        column1="fx_spot_id", column2="payment_id",
        string="Payments",
        copy=False, readonly=True,
    )
    payments_count = fields.Integer(
        string="Payments count", compute="_compute_payments_count",
    )
    payment_move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Payment Move Lines",
        compute="_compute_payments", store=True,
    )
    rate = fields.Float(
        required=True,
        readonly=True, states={"draft": [("readonly", False)]},
        digits=dp.get_precision('Exchange Rate'),
    )
    company_id = fields.Many2one(
        comodel_name="res.company", string="Company",
        change_default=True, required=True,
        readonly=True, states={"draft": [("readonly", False)]},
        default=lambda self: self.env.user.company_id,
    )
    company_currency_id = fields.Many2one(
        related="company_id.currency_id",
    )
    move_id = fields.Many2one(
        comodel_name="account.move", string="Journal Entry",
        readonly=True, copy=False,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal", string="Journal",
        required=True,
        default=lambda self: self.env.ref(
            "account_fx_spot.journal_account_fx_spot"),
        readonly=True, states={"draft": [("readonly", False)]},
    )
    reconciled = fields.Boolean(
        string="Paid/Reconciled", store=True,
        readonly=True, compute="_compute_residual",
    )
    comment = fields.Text(
        string="Additional Information",
        readonly=True, states={"draft": [("readonly", False)]},
    )

    @api.multi
    def _compute_payments_count(self):
        for rec in self:
            rec.payments_count = len(rec.payment_ids)

    @api.multi
    @api.depends("state", "payment_ids", "payment_ids.state",
                 "move_id.line_ids.amount_residual")
    def _compute_residual(self):
        """Computes residual amounts from Journal items."""
        for rec in self:
            in_residual = 0.0
            in_residual_company = 0.0
            out_residual = 0.0
            out_residual_company = 0.0
            for line in rec.sudo().move_id.line_ids:
                if line.account_id.internal_type == "receivable":
                    in_residual_company += line.amount_residual
                    if line.currency_id == rec.in_currency_id:
                        in_residual += line.amount_residual_currency if \
                            line.currency_id else line.amount_residual
                    else:
                        from_currency = (
                            (line.currency_id and line.currency_id.
                             with_context(date=line.date)) or
                            line.company_id.currency_id.
                            with_context(date=line.date))
                        in_residual += from_currency.compute(
                            line.amount_residual,
                            rec.in_currency_id)
                elif line.account_id.internal_type == "payable":
                    out_residual_company += line.amount_residual
                    if line.currency_id == rec.out_currency_id:
                        out_residual += line.amount_residual_currency if \
                            line.currency_id else line.amount_residual
                    else:
                        from_currency = (
                            (line.currency_id and line.currency_id.
                             with_context(date=line.date)) or
                            line.company_id.currency_id.
                            with_context(date=line.date))
                        out_residual += from_currency.compute(
                            line.amount_residual,
                            rec.out_currency_id)
            rec.residual_company_in = abs(in_residual_company)
            rec.residual_in = abs(in_residual)
            rec.residual_company_out = abs(out_residual_company)
            rec.residual_out = abs(out_residual)
            if (
                float_is_zero(
                    rec.residual_in,
                    precision_rounding=rec.in_currency_id.rounding) and
                float_is_zero(rec.residual_out,
                              precision_rounding=rec.out_currency_id.rounding)
            ):
                rec.reconciled = True
            else:
                rec.reconciled = False

    @api.multi
    @api.depends("move_id.line_ids.amount_residual")
    def _compute_payments(self):
        for rec in self:
            payment_lines = set()
            for line in rec.move_id.line_ids:
                payment_lines.update(line.mapped(
                    "matched_credit_ids.credit_move_id.id"))
                payment_lines.update(line.mapped(
                    "matched_debit_ids.debit_move_id.id"))
            rec.payment_move_line_ids = self.env[
                "account.move.line"].browse(list(payment_lines))

    @api.onchange("amount_out", "amount_in")
    def _onchange_amounts(self):
        self.rate = \
            self.amount_in / self.amount_out if self.amount_out else 0.0

    @api.onchange("rate")
    def _onchange_rate(self):
        self.amount_in = self.amount_out * self.rate

    def _prepare_account_move(self):
        self.ensure_one()
        if self.company_currency_id == self.in_currency_id:
            amount = self.amount_in
        elif self.company_id.currency_id != self.out_currency_id:
            amount = self.out_currency_id.compute(
                self.amount_out, self.company_id.currency_id)
        else:
            amount = self.amount_out
        receivable = {
            'name': '/',
            'debit': amount,
            'amount_currency': self.amount_in,
            'currency_id': self.in_currency_id.id,
            'account_id': self.partner_id.property_account_receivable_id.id,
            'partner_id': self.partner_id.id,
        }
        payable = {
            'name': '/',
            'credit': amount,
            'amount_currency': (-1) * self.amount_out,
            'currency_id': self.out_currency_id.id,
            'account_id': self.partner_id.property_account_payable_id.id,
            'partner_id': self.partner_id.id,
        }
        move_vals = {
            "name": self.name,
            "line_ids": [(0, 0, receivable), (0, 0, payable)],
            "journal_id": self.journal_id.id,
            "date": self.date_transaction,  # today
            "narration": self.comment,
        }
        return move_vals

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'account.fx.spot') or '/'
        return super(AccountFxSpot, self).create(vals)

    @api.multi
    def _write(self, vals):
        pre_not_reconciled = self.filtered(lambda r: not r.reconciled)
        pre_reconciled = self - pre_not_reconciled
        res = super(AccountFxSpot, self)._write(vals)
        reconciled = self.filtered(lambda r: r.reconciled)
        not_reconciled = self - reconciled
        (reconciled & pre_reconciled).filtered(
            lambda r: r.state == 'open').action_done()
        (not_reconciled & pre_not_reconciled).filtered(
            lambda r: r.state == 'done').action_re_open()
        return res

    @api.multi
    def register_payment(self, payment_line, writeoff_acc_id=False,
                         writeoff_journal_id=False):
        """Reconcile payable/receivable lines from the transaction
        with payment_line."""
        line_to_reconcile = self.env['account.move.line']
        reconcile_with = payment_line.account_id.internal_type
        for rec in self:
            line_to_reconcile += rec.move_id.line_ids.filtered(
                lambda r: not r.reconciled and
                r.account_id.internal_type == reconcile_with)
        return (line_to_reconcile + payment_line).reconcile(
            writeoff_acc_id, writeoff_journal_id)

    def action_confirm(self):
        acc_move_obj = self.env["account.move"]
        to_confirm = self.filtered(lambda r: r.state == 'draft')
        for rec in to_confirm:
            vals = rec._prepare_account_move()
            move = acc_move_obj.create(vals)
            move.post()
            rec.move_id = move
        to_confirm.write({'state': 'open'})
        return True

    @api.multi
    def action_done(self):
        to_pay_transactions = self.filtered(lambda r: r.state != "done")
        if to_pay_transactions.filtered(lambda r: r.state != "open"):
            raise UserError(_(
                "Transaction must be validated in order to set "
                "it to register payment."))
        if to_pay_transactions.filtered(lambda r: not r.reconciled):
            raise UserError(_(
                "You cannot pay an transaction which is partially paid. "
                "You need to reconcile payment entries first."))
        return to_pay_transactions.write({"state": "done"})

    @api.multi
    def action_re_open(self):
        if self.filtered(lambda r: r.state != "done"):
            raise UserError(_(
                "FX Spot Transaction must be done in order to set it to "
                "register payment."))
        return self.write({"state": "open"})

    def action_cancel(self):
        if self.filtered(lambda r: r.state not in ['draft', 'open']):
            raise UserError(_(
                "Transaction must be in draft or open state in order to "
                "be cancelled."))
        moves = self.env['account.move']
        for rec in self:
            if rec.move_id:
                moves += rec.move_id
            if rec.payment_move_line_ids:
                raise UserError(_(
                    'You cannot cancel a transaction which is partially paid. '
                    'You need to unreconcile related payment entries first.'))

        # First, set the transactions as cancelled and detach the move ids
        self.write({'state': 'cancel', 'move_id': False})
        if moves:
            # second, invalidate the move(s)
            moves.button_cancel()
            # delete the move this fx spot transaction was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            moves.unlink()
        return True

    @api.multi
    def action_draft(self):
        if self.filtered(lambda inv: inv.state != 'cancel'):
            raise UserError(_(
                "FX Spot Transaction must be cancelled in order to reset "
                "it to draft."))
        self.write({'state': 'draft', 'date_transaction': False})
        return True

    def action_view_payments(self):
        action = self.env.ref('account.action_account_payments')
        result = action.read()[0]
        payment_ids = self.payment_ids
        result['domain'] = [('id', 'in', payment_ids.ids)]
        return result
