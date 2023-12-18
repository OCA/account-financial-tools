# Copyright 2023 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    netting = fields.Boolean(
        help="Technical field, as user select invoice that are both AR and AP",
    )

    @api.model
    def default_get(self, fields_list):
        """
        Override the default behavior in case of netting.
        No account type checks are performed since netting allows
        the selection of multiple account types.
        """
        netting = self.env.context.get("netting")
        if netting and "line_ids" in fields_list:
            fields_list.remove("line_ids")
        res = super().default_get(fields_list)

        if netting:
            fields_list.append("line_ids")
            # Retrieve moves to pay from the context.

            if self._context.get("active_model") == "account.move":
                lines = (
                    self.env["account.move"]
                    .browse(self._context.get("active_ids", []))
                    .line_ids
                )
            elif self._context.get("active_model") == "account.move.line":
                lines = self.env["account.move.line"].browse(
                    self._context.get("active_ids", [])
                )
            else:
                raise UserError(
                    _(
                        "The register payment wizard should only be called on "
                        "account.move or account.move.line records."
                    )
                )

            if "journal_id" in res and not self.env["account.journal"].browse(
                res["journal_id"]
            ).filtered_domain(
                [
                    ("company_id", "=", lines.company_id.id),
                    ("type", "in", ("bank", "cash")),
                ]
            ):
                # default can be inherited from the list view, should be computed instead
                del res["journal_id"]

            # Keep lines having a residual amount to pay.
            available_lines = self.env["account.move.line"]
            for line in lines:
                if line.move_id.state != "posted":
                    raise UserError(
                        _("You can only register payment for posted journal entries.")
                    )

                if line.account_type not in ("asset_receivable", "liability_payable"):
                    continue
                if line.currency_id:
                    if line.currency_id.is_zero(line.amount_residual_currency):
                        continue
                else:
                    if line.company_currency_id.is_zero(line.amount_residual):
                        continue
                available_lines |= line

            # Check.
            if not available_lines:
                raise UserError(
                    _(
                        "You can't register a payment because there is nothing left "
                        "to pay on the selected journal items."
                    )
                )
            if len(lines.company_id) > 1:
                raise UserError(
                    _(
                        "You can't create payments for entries belonging "
                        "to different companies."
                    )
                )
            if len(lines.partner_id) > 1:
                raise UserError(_("All invoices must belong to same partner"))

            res.update(
                {
                    "line_ids": [Command.set(available_lines.ids)],
                    "netting": True,
                }
            )

        return res

    @api.model
    def _get_batch_communication(self, batch_result):
        if self.netting:
            labels = {
                line.name or line.move_id.ref or line.move_id.name
                for line in self.line_ids._origin
            }
            return ", ".join(sorted(labels))
        return super()._get_batch_communication(batch_result)

    def _create_payment_vals_from_wizard(self, batch_result):
        payment_vals = super()._create_payment_vals_from_wizard(batch_result)
        payment_vals["netting"] = self.netting
        return payment_vals

    @api.depends("line_ids")
    def _compute_from_lines(self):
        res = super()._compute_from_lines()
        for wizard in self:
            if not wizard.netting:
                continue

            batches = wizard._get_batches()
            balance = sum([sum(batch["lines"].mapped("balance")) for batch in batches])
            amount_currency = sum(
                [sum(batch["lines"].mapped("amount_currency")) for batch in batches]
            )
            if balance < 0.0:
                payment_type = "outbound"
            else:
                payment_type = "inbound"

            for batch in batches:
                if batch["payment_values"]["payment_type"] == payment_type:
                    batch_result = batch

            wizard_values_from_batch = wizard._get_wizard_values_from_batch(
                batch_result
            )
            wizard_values_from_batch["source_amount"] = abs(balance)
            wizard_values_from_batch["source_amount_currency"] = abs(amount_currency)
            wizard.update(wizard_values_from_batch)
            wizard.can_edit_wizard = True
            wizard.can_group_payments = True
        return res

    @api.depends("can_edit_wizard")
    def _compute_group_payment(self):
        res = super()._compute_group_payment()
        for wizard in self:
            if wizard.netting and wizard.can_edit_wizard:
                wizard.group_payment = True
        return res

    def _get_total_amount_in_wizard_currency_to_full_reconcile(
        self, batch_result, early_payment_discount=True
    ):
        self.ensure_one()
        if self.netting:
            all_batch = self._get_batches()
            # Get all value except first value
            filtered_list = all_batch[1:]
            for batch in filtered_list:
                batch_result["lines"] += batch["lines"]
        return super()._get_total_amount_in_wizard_currency_to_full_reconcile(
            batch_result, early_payment_discount
        )

    def _reconcile_netting(self, moves, payment_lines, domain):
        for move in moves:
            ml = move.line_ids.filtered_domain(domain)
            ml |= payment_lines.filtered(lambda l: l.name == move.name)
            ml.reconcile()

    def _netting_reconcile_payment(self, to_process):
        moveline_obj = self.env["account.move.line"]
        domain = [
            ("parent_state", "=", "posted"),
            ("account_type", "in", ("asset_receivable", "liability_payable")),
            ("reconciled", "=", False),
        ]
        moves = self.env["account.move"].browse(self.env.context.get("active_ids"))
        payment_lines = moveline_obj.search(
            domain + [("payment_id", "=", to_process[0]["payment"].id)]
        )
        self._reconcile_netting(moves, payment_lines, domain)

    def _reconcile_payments(self, to_process, edit_mode=False):
        if self.netting:
            return self._netting_reconcile_payment(to_process)
        return super()._reconcile_payments(to_process, edit_mode)
