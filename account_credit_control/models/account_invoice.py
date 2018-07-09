# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountInvoice(models.Model):
    """Check on cancelling of an invoice"""
    _inherit = 'account.invoice'

    credit_policy_id = fields.Many2one(
        'credit.control.policy',
        string='Credit Control Policy',
        help="The Credit Control Policy used for this "
             "invoice. If nothing is defined, it will "
             "use the account setting or the partner "
             "setting.",
        readonly=True,
        copy=False,
        groups="account_credit_control.group_account_credit_control_manager,"
               "account_credit_control.group_account_credit_control_user,"
               "account_credit_control.group_account_credit_control_info",
    )

    credit_control_line_ids = fields.One2many(
        'credit.control.line', 'invoice_id',
        string='Credit Lines',
        readonly=True,
        copy=False,
    )
    credit_control_notes = fields.Char(
        compute='_compute_credit_control_notes',
        inverse='_inverse_credit_control_notes',
        readonly=True,
        states={'open': [('readonly', False)]}
    )
    credit_control_date = fields.Date(
        compute='_compute_credit_control_date',
        inverse='_inverse_credit_control_date',
        string='Credit Control Ignore Before',
        readonly=True,
        states={'open': [('readonly', False)]}
    )

    @api.multi
    def _inverse_credit_control_notes(self):
        """
        Set credit control notes on every move line if invoice notes
        have been modified
        :return:
        """
        for invoice in self:
            line = invoice._get_payable_receivable_move_line()
            line.credit_control_notes = invoice.credit_control_notes

    @api.multi
    def _compute_credit_control_notes(self):
        for invoice in self:
            line = invoice._get_payable_receivable_move_line()
            invoice.credit_control_notes = line.credit_control_notes

    @api.multi
    def _get_payable_receivable_move_line(self):
        self.ensure_one()
        return self.move_id.line_ids.filtered(
            lambda l: l.account_id.internal_type in ['payable', 'receivable'])

    @api.multi
    def _inverse_credit_control_date(self):
        for invoice in self:
            line = invoice._get_payable_receivable_move_line()
            line.credit_control_date = invoice.credit_control_date

    @api.multi
    @api.depends('move_id.line_ids.credit_control_date',
                 'move_id.line_ids.invoice_id')
    def _compute_credit_control_date(self):
        for invoice in self:
            line = invoice._get_payable_receivable_move_line()
            invoice.credit_control_date = line.credit_control_date

    @api.multi
    def action_cancel(self):
        """Prevent to cancel invoice related to credit line"""
        # We will search if this invoice is linked with credit
        cc_line_obj = self.env['credit.control.line']
        for invoice in self:
            nondraft_domain = [('invoice_id', '=', invoice.id),
                               ('state', '!=', 'draft')]
            cc_nondraft_lines = cc_line_obj.search(nondraft_domain)
            if cc_nondraft_lines:
                raise UserError(
                    _('You cannot cancel this invoice.\n'
                      'A payment reminder has already been '
                      'sent to the customer.\n'
                      'You must create a credit note and '
                      'issue a new invoice.')
                )
            draft_domain = [('invoice_id', '=', invoice.id),
                            ('state', '=', 'draft')]
            cc_draft_line = cc_line_obj.search(draft_domain)
            cc_draft_line.unlink()
        return super(AccountInvoice, self).action_cancel()
