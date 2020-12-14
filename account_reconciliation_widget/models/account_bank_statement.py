from odoo import _, fields, models
from odoo.exceptions import UserError


class AccountBankStatement(models.Model):

    _inherit = "account.bank.statement"

    accounting_date = fields.Date(
        string="Accounting Date",
        help="If set, the accounting entries created during the bank statement "
        "reconciliation process will be created at this date.\n"
        "This is useful if the accounting period in which the entries should "
        "normally be booked is already closed.",
        states={"open": [("readonly", False)]},
        readonly=True,
    )

    def action_bank_reconcile_bank_statements(self):
        self.ensure_one()
        bank_stmt_lines = self.mapped("line_ids")
        return {
            "type": "ir.actions.client",
            "tag": "bank_statement_reconciliation_view",
            "context": {
                "statement_line_ids": bank_stmt_lines.ids,
                "company_ids": self.mapped("company_id").ids,
            },
        }


class AccountBankStatementLine(models.Model):

    _inherit = "account.bank.statement.line"

    move_name = fields.Char(
        string="Journal Entry Name",
        readonly=True,
        default=False,
        copy=False,
        help="Technical field holding the number given to the journal entry, "
        "automatically set when the statement line is reconciled then "
        "stored to set the same number again if the line is cancelled, "
        "set to draft and re-processed again.",
    )

    def process_reconciliation(
        self, counterpart_aml_dicts=None, payment_aml_rec=None, new_aml_dicts=None
    ):
        """Match statement lines with existing payments (eg. checks) and/or
        payables/receivables (eg. invoices and credit notes) and/or new move
        lines (eg. write-offs).
        If any new journal item needs to be created (via new_aml_dicts or
        counterpart_aml_dicts), a new journal entry will be created and will
        contain those items, as well as a journal item for the bank statement
        line.
        Finally, mark the statement line as reconciled by putting the matched
        moves ids in the column journal_entry_ids.

        :param self: browse collection of records that are supposed to have no
            accounting entries already linked.
        :param (list of dicts) counterpart_aml_dicts: move lines to create to
            reconcile with existing payables/receivables.
            The expected keys are :
            - 'name'
            - 'debit'
            - 'credit'
            - 'move_line'
                # The move line to reconcile (partially if specified
                # debit/credit is lower than move line's credit/debit)

        :param (list of recordsets) payment_aml_rec: recordset move lines
            representing existing payments (which are already fully reconciled)

        :param (list of dicts) new_aml_dicts: move lines to create. The expected
            keys are :
            - 'name'
            - 'debit'
            - 'credit'
            - 'account_id'
            - (optional) 'tax_ids'
            - (optional) Other account.move.line fields like analytic_account_id
                or analytics_id
            - (optional) 'reconcile_model_id'

        :returns: The journal entries with which the transaction was matched.
            If there was at least an entry in counterpart_aml_dicts or
            new_aml_dicts, this list contains the move created by the
            reconciliation, containing entries for the statement.line (1), the
            counterpart move lines (0..*) and the new move lines (0..*).
        """
        payable_account_type = self.env.ref("account.data_account_type_payable")
        receivable_account_type = self.env.ref("account.data_account_type_receivable")
        suspense_moves_mode = self._context.get("suspense_moves_mode")
        counterpart_aml_dicts = counterpart_aml_dicts or []
        payment_aml_rec = payment_aml_rec or self.env["account.move.line"]
        new_aml_dicts = new_aml_dicts or []

        aml_obj = self.env["account.move.line"]

        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency

        counterpart_moves = self.env["account.move"]

        # Check and prepare received data
        if any(rec.statement_id for rec in payment_aml_rec):
            raise UserError(_("A selected move line was already reconciled."))
        for aml_dict in counterpart_aml_dicts:
            if aml_dict["move_line"].reconciled and not suspense_moves_mode:
                raise UserError(_("A selected move line was already reconciled."))
            if isinstance(aml_dict["move_line"], int):
                aml_dict["move_line"] = aml_obj.browse(aml_dict["move_line"])

        account_types = self.env["account.account.type"]
        for aml_dict in counterpart_aml_dicts + new_aml_dicts:
            if aml_dict.get("tax_ids") and isinstance(aml_dict["tax_ids"][0], int):
                # Transform the value in the format required for One2many and
                # Many2many fields
                aml_dict["tax_ids"] = [(4, id, None) for id in aml_dict["tax_ids"]]

            user_type_id = (
                self.env["account.account"]
                .browse(aml_dict.get("account_id"))
                .user_type_id
            )
            if (
                user_type_id in [payable_account_type, receivable_account_type]
                and user_type_id not in account_types
            ):
                account_types |= user_type_id
        if suspense_moves_mode:
            if any(not line.journal_entry_ids for line in self):
                raise UserError(
                    _(
                        "Some selected statement line were not already "
                        "reconciled with an account move."
                    )
                )
        else:
            if any(line.journal_entry_ids for line in self):
                raise UserError(
                    _(
                        "A selected statement line was already reconciled with "
                        "an account move."
                    )
                )

        # Fully reconciled moves are just linked to the bank statement
        total = self.amount
        currency = self.currency_id or statement_currency
        for aml_rec in payment_aml_rec:
            balance = (
                aml_rec.amount_currency if aml_rec.currency_id else aml_rec.balance
            )
            aml_currency = aml_rec.currency_id or aml_rec.company_currency_id
            total -= aml_currency._convert(
                balance, currency, aml_rec.company_id, aml_rec.date
            )
            aml_rec.with_context(check_move_validity=False).write(
                {"statement_line_id": self.id}
            )
            counterpart_moves = counterpart_moves | aml_rec.move_id
            if (
                aml_rec.journal_id.post_at == "bank_rec"
                and aml_rec.payment_id
                and aml_rec.move_id.state == "draft"
            ):
                # In case the journal is set to only post payments when
                # performing bank reconciliation, we modify its date and post
                # it.
                aml_rec.move_id.date = self.date
                aml_rec.payment_id.payment_date = self.date
                aml_rec.move_id.post()
                # We check the paid status of the invoices reconciled with this
                # payment
                for invoice in aml_rec.payment_id.reconciled_invoice_ids:
                    self._check_invoice_state(invoice)

        # Create move line(s). Either matching an existing journal entry
        # (eg. invoice), in which case we reconcile the existing and the new
        # move lines together, or being a write-off.
        if counterpart_aml_dicts or new_aml_dicts:

            # Create the move
            self.sequence = self.statement_id.line_ids.ids.index(self.id) + 1
            move_vals = self._prepare_reconciliation_move(self.statement_id.name)
            if suspense_moves_mode:
                self.button_cancel_reconciliation()
            move = (
                self.env["account.move"]
                .with_context(default_journal_id=move_vals["journal_id"])
                .create(move_vals)
            )
            counterpart_moves = counterpart_moves | move

            # Create The payment
            payment = self.env["account.payment"]
            partner_id = (
                self.partner_id
                or (aml_dict.get("move_line") and aml_dict["move_line"].partner_id)
                or self.env["res.partner"]
            )
            if abs(total) > 0.00001:
                payment_vals = self._prepare_payment_vals(total)
                if not payment_vals["partner_id"]:
                    payment_vals["partner_id"] = partner_id.id
                if payment_vals["partner_id"] and len(account_types) == 1:
                    payment_vals["partner_type"] = (
                        "customer"
                        if account_types == receivable_account_type
                        else "supplier"
                    )
                payment = payment.create(payment_vals)

            # Complete dicts to create both counterpart move lines and write-offs
            to_create = counterpart_aml_dicts + new_aml_dicts
            date = self.date or fields.Date.today()
            for aml_dict in to_create:
                aml_dict["move_id"] = move.id
                aml_dict["partner_id"] = self.partner_id.id
                aml_dict["statement_line_id"] = self.id
                self._prepare_move_line_for_currency(aml_dict, date)

            # Create write-offs
            for aml_dict in new_aml_dicts:
                aml_dict["payment_id"] = payment and payment.id or False
                aml_obj.with_context(check_move_validity=False).create(aml_dict)

            # Create counterpart move lines and reconcile them
            for aml_dict in counterpart_aml_dicts:
                if (
                    aml_dict["move_line"].payment_id
                    and not aml_dict["move_line"].statement_line_id
                ):
                    aml_dict["move_line"].write({"statement_line_id": self.id})
                if aml_dict["move_line"].partner_id.id:
                    aml_dict["partner_id"] = aml_dict["move_line"].partner_id.id
                aml_dict["account_id"] = aml_dict["move_line"].account_id.id
                aml_dict["payment_id"] = payment and payment.id or False

                counterpart_move_line = aml_dict.pop("move_line")
                new_aml = aml_obj.with_context(check_move_validity=False).create(
                    aml_dict
                )

                (new_aml | counterpart_move_line).reconcile()

                self._check_invoice_state(counterpart_move_line.move_id)

            # Balance the move
            st_line_amount = -sum([x.balance for x in move.line_ids])
            aml_dict = self._prepare_reconciliation_move_line(move, st_line_amount)
            aml_dict["payment_id"] = payment and payment.id or False
            aml_obj.with_context(check_move_validity=False).create(aml_dict)

            # Needs to be called manually as lines were created 1 by 1
            move.update_lines_tax_exigibility()
            move.post()
            # record the move name on the statement line to be able to retrieve
            # it in case of unreconciliation
            self.write({"move_name": move.name})
            payment and payment.write({"payment_reference": move.name})
        elif self.move_name:
            raise UserError(
                _(
                    "Operation not allowed. Since your statement line already "
                    "received a number (%s), you cannot reconcile it entirely "
                    "with existing journal entries otherwise it would make a "
                    "gap in the numbering. You should book an entry and make a "
                    "regular revert of it in case you want to cancel it."
                )
                % (self.move_name)
            )

        # create the res.partner.bank if needed
        if self.account_number and self.partner_id and not self.bank_account_id:
            # Search bank account without partner to handle the case the
            # res.partner.bank already exists but is set on a different partner.
            self.bank_account_id = self._find_or_create_bank_account()

        counterpart_moves._check_balanced()
        return counterpart_moves

    def _prepare_reconciliation_move(self, move_ref):
        """Prepare the dict of values to create the move from a statement line.
         This method may be overridden to adapt domain logic through model
         inheritance (make sure to call super() to establish a clean extension
         chain).

        :param char move_ref: will be used as the reference of the generated
            account move
        :return: dict of value to create() the account.move
        """
        ref = move_ref or ""
        if self.ref:
            ref = move_ref + " - " + self.ref if move_ref else self.ref
        data = {
            "type": "entry",
            "journal_id": self.statement_id.journal_id.id,
            "currency_id": self.statement_id.currency_id.id,
            "date": self.statement_id.accounting_date or self.date,
            "partner_id": self.partner_id.id,
            "ref": ref,
        }
        if self.move_name:
            data.update(name=self.move_name)
        return data

    def _prepare_reconciliation_move_line(self, move, amount):
        """Prepare the dict of values to balance the move.

        :param recordset move: the account.move to link the move line
        :param dict move: a dict of vals of a account.move which will be created
            later
        :param float amount: the amount of transaction that wasn't already
            reconciled
        """
        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency
        amount_currency = False
        st_line_currency_rate = (
            self.currency_id and (self.amount_currency / self.amount) or False
        )
        if isinstance(move, dict):
            amount_sum = sum(x[2].get("amount_currency", 0) for x in move["line_ids"])
        else:
            amount_sum = sum(x.amount_currency for x in move.line_ids)
        # We have several use case here to compare the currency and amount
        # currency of counterpart line to balance the move:
        if (
            st_line_currency != company_currency
            and st_line_currency == statement_currency
        ):
            # company in currency A, statement in currency B and transaction in
            # currency B
            # counterpart line must have currency B and correct amount is
            # inverse of already existing lines
            amount_currency = -amount_sum
        elif (
            st_line_currency != company_currency
            and statement_currency == company_currency
        ):
            # company in currency A, statement in currency A and transaction in
            # currency B
            # counterpart line must have currency B and correct amount is
            # inverse of already existing lines
            amount_currency = -amount_sum
        elif (
            st_line_currency != company_currency
            and st_line_currency != statement_currency
        ):
            # company in currency A, statement in currency B and transaction in
            # currency C
            # counterpart line must have currency B and use rate between B and
            # C to compute correct amount
            amount_currency = -amount_sum / st_line_currency_rate
        elif (
            st_line_currency == company_currency
            and statement_currency != company_currency
        ):
            # company in currency A, statement in currency B and transaction in
            # currency A
            # counterpart line must have currency B and amount is computed using
            # the rate between A and B
            amount_currency = amount / st_line_currency_rate

        # last case is company in currency A, statement in currency A and
        # transaction in currency A
        # and in this case counterpart line does not need any second currency
        # nor amount_currency

        # Check if default_debit or default_credit account are properly configured
        account_id = (
            amount >= 0
            and self.statement_id.journal_id.default_credit_account_id.id
            or self.statement_id.journal_id.default_debit_account_id.id
        )

        if not account_id:
            raise UserError(
                _(
                    "No default debit and credit account defined on journal %s "
                    "(ids: %s)."
                    % (
                        self.statement_id.journal_id.name,
                        self.statement_id.journal_id.ids,
                    )
                )
            )

        aml_dict = {
            "name": self.name,
            "partner_id": self.partner_id and self.partner_id.id or False,
            "account_id": account_id,
            "credit": amount < 0 and -amount or 0.0,
            "debit": amount > 0 and amount or 0.0,
            "statement_line_id": self.id,
            "currency_id": statement_currency != company_currency
            and statement_currency.id
            or (st_line_currency != company_currency and st_line_currency.id or False),
            "amount_currency": amount_currency,
        }
        if isinstance(move, self.env["account.move"].__class__):
            aml_dict["move_id"] = move.id
        return aml_dict

    def _get_communication(self, payment_method_id):
        return self.name or ""

    def _prepare_payment_vals(self, total):
        """Prepare the dict of values to create the payment from a statement
         line. This method may be overridden for update dict
         through model inheritance (make sure to call super() to establish a
         clean extension chain).

        :param float total: will be used as the amount of the generated payment
        :return: dict of value to create() the account.payment
        """
        self.ensure_one()
        partner_type = False
        if self.partner_id:
            if total < 0:
                partner_type = "supplier"
            else:
                partner_type = "customer"
        if not partner_type and self.env.context.get("default_partner_type"):
            partner_type = self.env.context["default_partner_type"]
        currency = self.journal_id.currency_id or self.company_id.currency_id
        payment_methods = (
            (total > 0)
            and self.journal_id.inbound_payment_method_ids
            or self.journal_id.outbound_payment_method_ids
        )
        return {
            "payment_method_id": payment_methods and payment_methods[0].id or False,
            "payment_type": total > 0 and "inbound" or "outbound",
            "partner_id": self.partner_id.id,
            "partner_type": partner_type,
            "journal_id": self.statement_id.journal_id.id,
            "payment_date": self.date,
            "state": "reconciled",
            "currency_id": currency.id,
            "amount": abs(total),
            "communication": self._get_communication(
                payment_methods[0] if payment_methods else False
            ),
            "name": self.statement_id.name or _("Bank Statement %s") % self.date,
        }

    def _prepare_move_line_for_currency(self, aml_dict, date):
        self.ensure_one()
        company_currency = self.journal_id.company_id.currency_id
        statement_currency = self.journal_id.currency_id or company_currency
        st_line_currency = self.currency_id or statement_currency
        st_line_currency_rate = (
            self.currency_id and (self.amount_currency / self.amount) or False
        )
        company = self.company_id

        if st_line_currency.id != company_currency.id:
            aml_dict["amount_currency"] = aml_dict["debit"] - aml_dict["credit"]
            aml_dict["currency_id"] = st_line_currency.id
            if (
                self.currency_id
                and statement_currency.id == company_currency.id
                and st_line_currency_rate
            ):
                # Statement is in company currency but the transaction is in
                # foreign currency
                aml_dict["debit"] = company_currency.round(
                    aml_dict["debit"] / st_line_currency_rate
                )
                aml_dict["credit"] = company_currency.round(
                    aml_dict["credit"] / st_line_currency_rate
                )
            elif self.currency_id and st_line_currency_rate:
                # Statement is in foreign currency and the transaction is in
                # another one
                aml_dict["debit"] = statement_currency._convert(
                    aml_dict["debit"] / st_line_currency_rate,
                    company_currency,
                    company,
                    date,
                )
                aml_dict["credit"] = statement_currency._convert(
                    aml_dict["credit"] / st_line_currency_rate,
                    company_currency,
                    company,
                    date,
                )
            else:
                # Statement is in foreign currency and no extra currency is
                # given for the transaction
                aml_dict["debit"] = st_line_currency._convert(
                    aml_dict["debit"], company_currency, company, date
                )
                aml_dict["credit"] = st_line_currency._convert(
                    aml_dict["credit"], company_currency, company, date
                )
        elif statement_currency.id != company_currency.id:
            # Statement is in foreign currency but the transaction is in company
            # currency
            prorata_factor = (
                aml_dict["debit"] - aml_dict["credit"]
            ) / self.amount_currency
            aml_dict["amount_currency"] = prorata_factor * self.amount
            aml_dict["currency_id"] = statement_currency.id

    def _check_invoice_state(self, invoice):
        if invoice.is_invoice(include_receipts=True):
            invoice._compute_amount()
