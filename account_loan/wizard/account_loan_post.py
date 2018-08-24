
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountLoanPost(models.TransientModel):
    _name = "account.loan.post"

    @api.model
    def _default_journal_id(self):
        loan_id = self._context.get('default_loan_id')
        if loan_id:
            return self.env['account.loan'].browse(loan_id).journal_id.id

    @api.model
    def _default_account_id(self):
        loan_id = self._context.get('default_loan_id')
        if loan_id:
            loan = self.env['account.loan'].browse(loan_id)
            if loan.is_leasing:
                return loan.leased_asset_account_id.id
            else:
                return loan.partner_id.with_context(
                    force_company=loan.company_id.id
                ).property_account_receivable_id.id

    loan_id = fields.Many2one(
        'account.loan',
        required=True,
        readonly=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        required=True,
        default=_default_journal_id
    )
    account_id = fields.Many2one(
        'account.account',
        required=True,
        default=_default_account_id
    )

    def move_line_vals(self):
        res = list()
        partner = self.loan_id.partner_id.with_context(
            force_company=self.loan_id.company_id.id)
        line = self.loan_id.line_ids.filtered(lambda r: r.sequence == 1)
        res.append({
            'account_id': self.account_id.id,
            'partner_id': partner.id,
            'credit': 0,
            'debit': line.pending_principal_amount,
        })
        if (
            line.pending_principal_amount -
            line.long_term_pending_principal_amount > 0
        ):
            res.append({
                'name': self.loan_id.name,
                'account_id': self.loan_id.short_term_loan_account_id.id,
                'credit': (line.pending_principal_amount -
                           line.long_term_pending_principal_amount),
                'debit': 0,
                'analytic_account_id': self.loan_id.account_analytic_id.id,
            })
        if (
            line.long_term_pending_principal_amount > 0 and
            self.loan_id.long_term_loan_account_id
        ):
            res.append({
                'name': self.loan_id.name,
                'account_id': self.loan_id.long_term_loan_account_id.id,
                'credit': line.long_term_pending_principal_amount,
                'debit': 0,
                'analytic_account_id': self.loan_id.account_analytic_id.id,
            })

        return res

    def move_vals(self):
        if not self.loan_id.start_date:
            date = fields.Datetime.now()
        else:
            date = self.loan_id.start_date
        return {
            'loan_id': self.loan_id.id,
            'date': date,
            'ref': self.loan_id.name,
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, vals) for vals in self.move_line_vals()]
        }

    def invoice_line_vals(self):
        vals = list()
        vals.append({
            'name': "Down Payment",
            'quantity': 1,
            'price_unit': self.loan_id.down_payment,
            'account_id': self.loan_id.short_term_loan_account_id.id,
            'account_analytic_id': self.loan_id.account_analytic_id.id
        })
        return vals

    @api.multi
    def run(self):
        self.ensure_one()
        self.loan_id.create_analytic_account()
        if self.loan_id.state != 'draft':
            raise UserError(_('Only loans in draft state can be posted'))
        if not self.loan_id.is_down_payment:
            self.loan_id.post()
        move_orig = self.env['account.move'].create(self.move_vals())
        move_orig.post()
        if self.loan_id.is_down_payment and self.loan_id.is_leasing:
            partner = self.loan_id.partner_id.with_context(
                force_company=self.loan_id.company_id.id)
            invoice = self.env['account.invoice'].create(
                {
                    'loan_id': self.loan_id.id,
                    'type': 'in_invoice',
                    'partner_id': self.loan_id.partner_id.id,
                    'date_invoice': fields.Datetime.now(),
                    'account_id': partner.property_account_payable_id.id,
                    'journal_id': self.loan_id.journal_id.id,
                    'company_id': self.loan_id.company_id.id,
                    'invoice_line_ids': [(0, 0, vals) for vals in
                                         self.invoice_line_vals()]
                })
            invoice.action_invoice_open()
            self.loan_id.post()
        elif self.loan_id.is_down_payment and not self.loan_id.is_leasing:
            vals = []
            vals.append({
                'name': self.loan_id.name,
                'account_id': self.loan_id.partner_id.property_account_payable_id.id,
                'partner_id': self.loan_id.partner_id.id,
                'credit': self.loan_id.down_payment,
                'debit': 0,
            })
            vals.append({
                'name': self.loan_id.name,
                'account_id': self.loan_id.short_term_loan_account_id.id,
                'credit': 0,
                'debit': self.loan_id.down_payment,
                'analytic_account_id': self.loan_id.account_analytic_id.id,
            })
            move = self.env['account.move'].create({
                'loan_id': self.loan_id.id,
                'date': fields.Datetime.now(),
                'ref': self.loan_id.name,
                'journal_id': self.loan_id.journal_id.id,
                'line_ids': [(0, 0, val) for val in vals]

            })
            move.post()
            self.loan_id.post()
        else:
            pass


