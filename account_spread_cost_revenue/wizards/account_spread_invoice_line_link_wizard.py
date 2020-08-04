# Copyright 2018-2019 Onestein (<https://www.onestein.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class AccountSpreadInvoiceLineLinkWizard(models.TransientModel):
    _name = 'account.spread.invoice.line.link.wizard'
    _description = 'Account Spread Invoice Line Link Wizard'

    def _selection_spread_action_type(self):
        base_selection = [
            ('template', _('Create from spread template')),
            ('new', _('Create new spread board'))
        ]
        if not self.env.context.get('allow_spread_planning'):
            return base_selection

        link_selection = [
            ('link', _('Link to existing spread board')),
        ]
        return link_selection + base_selection

    def _selection_default_spread_action_type(self):
        if not self.env.context.get('allow_spread_planning'):
            return 'template'
        return 'link'

    invoice_line_id = fields.Many2one(
        'account.invoice.line',
        string='Invoice Line',
        readonly=True,
        required=True,
        ondelete='cascade')
    invoice_id = fields.Many2one(
        related='invoice_line_id.invoice_id',
        readonly=True)
    invoice_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('out_refund', 'Customer Credit Note'),
        ('in_refund', 'Vendor Credit Note')],
        compute='_compute_invoice_type',
        store=True)
    spread_type = fields.Selection([
        ('sale', 'Customer'),
        ('purchase', 'Supplier')],
        compute='_compute_invoice_type',
        store=True)
    spread_id = fields.Many2one(
        'account.spread',
        string='Spread Board')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True)
    spread_action_type = fields.Selection(
        selection=_selection_spread_action_type,
        default=_selection_default_spread_action_type)
    template_id = fields.Many2one(
        'account.spread.template',
        string='Spread Template')
    use_invoice_line_account = fields.Boolean(
        string="Use invoice line's account",
        help="Use invoice line's account as Balance sheet / spread account.\n"
        "In this case, user need to select expense/revenue account too.")
    spread_account_id = fields.Many2one(
        'account.account',
        string='Balance sheet account / Spread account',
        store=True)
    exp_rev_account_id = fields.Many2one(
        'account.account',
        string='Expense/revenue account',
        help="Optional account to overwrite the existing expense/revenue "
             "account")
    spread_journal_id = fields.Many2one(
        'account.journal',
        string='Spread Journal',
        store=True)

    @api.depends('invoice_line_id')
    def _compute_invoice_type(self):
        for wizard in self:
            invoice = wizard.invoice_line_id.invoice_id
            wizard.invoice_type = invoice.type
            if invoice.type in ['out_invoice', 'out_refund']:
                wizard.spread_type = 'sale'
            else:
                wizard.spread_type = 'purchase'

    @api.onchange('company_id', 'invoice_type')
    def _onchange_spread_journal_account(self):
        for wizard in self:
            company = wizard.company_id
            acc_revenue = company.default_spread_revenue_account_id
            acc_expense = company.default_spread_expense_account_id
            journal_revenue = company.default_spread_revenue_journal_id
            journal_expense = company.default_spread_expense_journal_id
            if wizard.invoice_type in ('out_invoice', 'in_refund'):
                wizard.spread_account_id = acc_revenue
                wizard.spread_journal_id = journal_revenue
            else:
                wizard.spread_account_id = acc_expense
                wizard.spread_journal_id = journal_expense

    @api.multi
    def _inverse_spread_journal_account(self):
        """Keep this for making the fields editable"""
        pass

    @api.onchange('invoice_type')
    def onchange_invoice_type(self):
        domain = [
            ('invoice_id', '=', False),
            ('invoice_type', '=', self.invoice_type),
            ('company_id', '=', self.company_id.id)]
        res = {'domain': {'spread_id': domain}}
        return res

    @api.onchange('use_invoice_line_account')
    def _onchange_user_invoice_line_account(self):
        self.spread_account_id = (self.use_invoice_line_account and
                                  self.invoice_line_id.account_id or False)
        self.exp_rev_account_id = False

    @api.multi
    def confirm(self):
        self.ensure_one()

        if self.spread_action_type == 'link':
            if not self.invoice_line_id.spread_id:
                self.invoice_line_id.spread_id = self.spread_id

            return {
                'name': _('Spread Details'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.spread',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'readonly': False,
                'res_id': self.invoice_line_id.spread_id.id,
            }
        elif self.spread_action_type == 'new':
            debit_account = credit_account = self.spread_account_id
            if self.invoice_type in ('out_invoice', 'in_refund'):
                credit_account = (self.exp_rev_account_id or
                                  self.invoice_line_id.account_id)
            else:
                debit_account = (self.exp_rev_account_id or
                                 self.invoice_line_id.account_id)

            analytic_account = self.invoice_line_id.account_analytic_id
            analytic_tags = self.invoice_line_id.analytic_tag_ids
            date_invoice = self.invoice_id.date_invoice or fields.Date.today()
            use_il_account = self.use_invoice_line_account

            return {
                'name': _('New Spread Board'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.spread',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'readonly': False,
                'context': {
                    'default_name': self.invoice_line_id.name,
                    'default_invoice_type': self.invoice_type,
                    'default_invoice_line_id': self.invoice_line_id.id,
                    'default_use_invoice_line_account': use_il_account,
                    'default_debit_account_id': debit_account.id,
                    'default_credit_account_id': credit_account.id,
                    'default_journal_id': self.spread_journal_id.id,
                    'default_account_analytic_id': analytic_account.id,
                    'default_analytic_tag_ids': analytic_tags.ids,
                    'default_spread_date': date_invoice,
                },
            }
        elif self.spread_action_type == 'template':
            if not self.invoice_line_id.spread_id:
                account = self.invoice_line_id.account_id
                spread_account_id = False
                if self.template_id.use_invoice_line_account:
                    account = self.template_id.exp_rev_account_id
                    spread_account_id = self.invoice_line_id.account_id.id

                spread_vals = self.template_id._prepare_spread_from_template(
                    spread_account_id=spread_account_id
                )
                date_invoice = self.invoice_id.date_invoice
                date_invoice = date_invoice or self.template_id.start_date
                date_invoice = date_invoice or fields.Date.today()
                spread_vals['spread_date'] = date_invoice

                spread_vals['name'] = ('%s %s') % (
                    spread_vals['name'],
                    self.invoice_line_id.name
                )

                if spread_vals['invoice_type'] == 'out_invoice':
                    spread_vals['credit_account_id'] = account.id
                else:
                    spread_vals['debit_account_id'] = account.id

                analytic_account = self.invoice_line_id.account_analytic_id
                spread_vals['account_analytic_id'] = analytic_account.id

                spread = self.env['account.spread'].create(spread_vals)

                analytic_tags = self.invoice_line_id.analytic_tag_ids
                spread.analytic_tag_ids = analytic_tags

                self.invoice_line_id.spread_id = spread
            return {
                'name': _('Spread Details'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.spread',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'readonly': False,
                'res_id': self.invoice_line_id.spread_id.id,
            }
