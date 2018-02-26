# -*- coding: utf-8 -*-
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
                'account_id': self.loan_id.short_term_loan_account_id.id,
                'credit': (line.pending_principal_amount -
                           line.long_term_pending_principal_amount),
                'debit': 0,
            })
        if (
            line.long_term_pending_principal_amount > 0 and
            self.loan_id.long_term_loan_account_id
        ):
            res.append({
                'account_id': self.loan_id.long_term_loan_account_id.id,
                'credit': line.long_term_pending_principal_amount,
                'debit': 0,
            })

        return res

    def move_vals(self):
        return {
            'loan_id': self.loan_id.id,
            'date': self.loan_id.start_date,
            'ref': self.loan_id.name,
            'journal_id': self.journal_id.id,
            'line_ids': [(0, 0, vals) for vals in self.move_line_vals()]
        }

    @api.multi
    def run(self):
        self.ensure_one()
        if self.loan_id.state != 'draft':
            raise UserError(_('Only loans in draft state can be posted'))
        self.loan_id.post()
        move = self.env['account.move'].create(self.move_vals())
        move.post()
