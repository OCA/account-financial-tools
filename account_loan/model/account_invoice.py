# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    loan_line_id = fields.Many2one(
        'account.loan.line',
        readonly=True,
        ondelete='restrict',
    )
    loan_id = fields.Many2one(
        'account.loan',
        readonly=True,
        store=True,
        ondelete='restrict',
    )

    @api.multi
    def action_move_create(self):
        if self.loan_line_id:
            return super(AccountInvoice, self.with_context(
                default_loan_line_id=self.loan_line_id.id,
                default_loan_id=self.loan_id.id,
            )).action_move_create()
        return super(AccountInvoice, self).action_move_create()

    @api.multi
    def finalize_invoice_move_lines(self, move_lines):
        vals = super(AccountInvoice, self).finalize_invoice_move_lines(move_lines)
        if self.loan_line_id:
            ll = self.loan_line_id
            if (
                ll.long_term_loan_account_id and
                ll.long_term_principal_amount != 0
            ):
                vals.append((0, 0, {
                    'account_id': ll.loan_id.short_term_loan_account_id.id,
                    'credit': ll.long_term_principal_amount,
                    'debit': 0,
                }))
                vals.append((0, 0, {
                    'name': ll.loan_id.name,
                    'account_id': ll.long_term_loan_account_id.id,
                    'credit': 0,
                    'debit': ll.long_term_principal_amount,
                    'analytic_account_id': ll.loan_id.account_analytic_id.id
                }))
        return vals
