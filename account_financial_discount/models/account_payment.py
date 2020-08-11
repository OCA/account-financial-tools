# Copyright 2019-2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    force_financial_discount = fields.Boolean(
        'Force financial discount?',
        help='Force financial discount even if the date is past and the flag is'
        ' not set on the invoices.',
    )
    show_force_financial_discount = fields.Boolean()

    @api.model
    def _compute_payment_amount(self, invoices, currency, journal, date):
        """Override odoo function to take financial discounts into account."""
        # Get the payment invoices
        total = super()._compute_payment_amount(
            invoices, currency, journal, date
        )
        if not invoices:
            return total

        company = journal.company_id
        currency = currency or journal.currency_id or company.currency_id
        date = date or fields.Date.today()

        self.env.cr.execute(
            r'''
            SELECT
                move.type AS type,
                move.currency_id AS currency_id,
                move.force_financial_discount AS force_financial_discount,
                line.date_discount AS date_discount,
                SUM(line.amount_discount) as amount_discount,
                SUM(line.amount_discount_currency) as amount_discount_currency
            FROM account_move move
            LEFT JOIN account_move_line line ON line.move_id = move.id
            LEFT JOIN account_account account ON account.id = line.account_id
            LEFT JOIN account_account_type account_type ON account_type.id = account.user_type_id
            WHERE move.id IN %s
            AND account_type.type IN ('receivable', 'payable')
            GROUP BY move.id, move.type, line.date_discount
        ''',
            [tuple(invoices.ids)],
        )
        query_res = self._cr.dictfetchall()
        for res in query_res:
            # force_financial_discount should be handled differently according
            # to the context in which _compute_payment_amount is called:
            #   - account.payment.default_get > meaning we should check if the
            #     flag is set on the moves
            #   - account.payment._onchange_force_financial_discount > meaning
            #     we should check in the context of invoices if flag is set
            #   - account.payment.compute_payment_difference > meaning we
            #     should not deduce discount for the difference as it was for
            #     the amount (bypass_financial_discount on self)
            #   - account.payment.register._prepare_payment_vals > meaning we
            #     should check in the context of invoices if flag is set
            if (
                not self.env.context.get('bypass_financial_discount')
                and res['date_discount']
                and (
                    fields.Date.from_string(res['date_discount']) >= date
                    or res['force_financial_discount']
                    or invoices.env.context.get('force_financial_discount')
                )
            ):
                move_currency = self.env['res.currency'].browse(
                    res['currency_id']
                )
                if (
                    move_currency == currency
                    and move_currency != company.currency_id
                ):
                    total -= res['amount_discount_currency']
                else:
                    total -= company.currency_id._convert(
                        res['amount_discount'], currency, company, date
                    )
        return total

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        active_ids = self.env.context.get(
            'active_ids'
        ) or self.env.context.get('active_id')
        active_model = self._context.get('active_model')
        if not active_ids or active_model != 'account.move':
            return values
        invoices = self.env['account.move'].browse(active_ids)
        if (
            'show_force_financial_discount' in fields_list
            and 'show_force_financial_discount' not in values
        ):
            # TODO Debug all cases and make this more explicit?
            # If at least one invoice has discounts on its move lines
            any_invoice_with_discount = any(
                invoices.mapped('line_ids.amount_discount')
            )
            # If not all invoices have discounts available
            not_all_invoices_with_discounts_available = not all(
                invoices.mapped('has_discount_available')
            )
            # If any invoice has force_financial_discount
            any_invoice_with_forced_discount = any(
                invoices.mapped('force_financial_discount')
            )
            # Display the button only if there are invoices with late discounts
            values['show_force_financial_discount'] = (
                any_invoice_with_forced_discount
                or any_invoice_with_discount
                and not_all_invoices_with_discounts_available
            )
        # Set force_financial_discount according to active invoices
        if (
            'force_financial_discount' in fields_list
            and 'force_financial_discount' not in values
        ):
            if all(invoices.mapped('force_financial_discount')):
                values['force_financial_discount'] = True
        # Add the writeoff account set on the company as a default.
        if 'writeoff_account_id' in fields_list:
            company = self.env.user.company_id
            if 'payment_type' in values:
                if values['payment_type'] == 'outbound':
                    values[
                        'writeoff_account_id'
                    ] = company.financial_discount_revenue_account_id.id
                elif values['payment_type'] == 'inbound':
                    values[
                        'writeoff_account_id'
                    ] = company.financial_discount_expense_account_id.id
            # TODO As writeoff_label is not translatable, keep the string in english?
            #  We should probably move this somewhere so same label can be used
            #  from bank statement reconciliation?
            values['writeoff_label'] = _('Financial Discount')
            values['payment_difference_handling'] = 'reconcile'
        return values

    @api.onchange('force_financial_discount')
    def _onchange_force_financial_discount(self):
        """Recompute amount and payment difference when force_financial_discount
        is changed.
        """
        active_ids = self._context.get('active_ids') or self._context.get(
            'active_id'
        )
        active_model = self._context.get('active_model')
        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return
        invoices = (
            self.env['account.move']
            .browse(active_ids)
            .filtered(lambda move: move.is_invoice(include_receipts=True))
        )
        self.amount = abs(
            self._compute_payment_amount(
                # we have to pass this through the context, because
                # _compute_payment_amount is a model method (can't use the field)
                invoices.with_context(
                    force_financial_discount=self.force_financial_discount
                ),
                fields.first(invoices).currency_id,
                fields.first(invoices).journal_id,
                self.payment_date,
            )
        )
        self._compute_payment_difference()

    @api.onchange('currency_id')
    def _onchange_currency(self):
        return super(
            AccountPayment,
            self.with_context(
                force_financial_discount=self.force_financial_discount
            ),
        )._onchange_currency()

    @api.onchange('journal_id')
    def _onchange_journal(self):
        return super(
            AccountPayment,
            self.with_context(
                force_financial_discount=self.force_financial_discount
            ),
        )._onchange_journal()

    @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id')
    def _compute_payment_difference(self):
        """Recompute the payment difference.

        The payment difference is the discount that will be
        written on the writeoff account.
        """
        # for pay in self.filtered(lambda p: p.invoice_ids):
        #     pay.payment_difference = pay.get_discount_for_invoices(
        #         pay.invoice_ids
        #     )
        return super(
            AccountPayment, self.with_context(bypass_financial_discount=True)
        )._compute_payment_difference()

    def get_discount_for_invoices(self, invoices):
        """Get the total discount for all the invoices in the payment.
        """
        # TODO check usage from report
        amount_discount = 0
        for inv in invoices:
            pterm_line = inv._get_first_payment_term_line()
            if inv.currency_id == self.currency_id:
                amount_discount += (
                    pterm_line.amount_discount_currency
                    or pterm_line.amount_discount
                )
            else:
                amount_discount += inv.currency_id._convert(
                    pterm_line.amount_discount_currency
                    or pterm_line.amount_discount,
                    self.currency_id,
                    self.env.user.company_id,
                    self.payment_date or fields.Date.today(),
                )
        return amount_discount


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    force_financial_discount = fields.Boolean(
        string='Apply Financial Discount Past Date',
        help='Force financial discount even if the date is past and the flag is'
        ' not set on the invoices.\n'
        'Note that financial discounts will be applied for invoices having'
        'the flag set, even if this checkbox is not marked.',
    )
    show_force_financial_discount = fields.Boolean()

    @api.model
    def default_get(self, fields_list):
        values = super().default_get(fields_list)
        if (
            'show_force_financial_discount' in fields_list
            and 'show_force_financial_discount' not in values
        ):
            active_ids = self.env.context.get('active_ids')
            invoices = self.env['account.move'].browse(active_ids)
            # If at least one invoice has discounts on its move lines
            any_invoice_with_discount = any(
                invoices.mapped('line_ids.amount_discount')
            )
            # If not all invoices have discounts available
            not_all_invoices_with_discounts_available = not all(
                invoices.mapped('has_discount_available')
            )
            # If any invoice has force_financial_discount
            any_invoice_with_forced_discount = any(
                invoices.mapped('force_financial_discount')
            )
            # Display the button only if there are invoices with late discounts
            values['show_force_financial_discount'] = (
                any_invoice_with_forced_discount
                or any_invoice_with_discount
                and not_all_invoices_with_discounts_available
            )
        return values

    def _prepare_payment_vals(self, invoices):
        """Extend payment_vals with force_financial_discount."""
        res = super()._prepare_payment_vals(
            invoices.with_context(
                force_financial_discount=self.force_financial_discount
            )
        )
        if len(invoices) == 1:
            res['force_financial_discount'] = invoices.force_financial_discount
        else:
            res['force_financial_discount'] = self.force_financial_discount
        return res
