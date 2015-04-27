# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, AUTHORS file in root directory
##############################################################################
from openerp.exceptions import Warning
from openerp import models, fields, api, _


class account_check_dreject(models.TransientModel):
    _name = 'account.check.dreject'

    @api.model
    def _get_company_id(self):
        active_ids = self._context.get('active_ids', [])
        checks = self.env['account.check'].browse(active_ids)
        company_ids = [x.company_id.id for x in checks]
        if len(set(company_ids)) > 1:
            raise Warning(_('All checks must be from the same company!'))
        return self.env['res.company'].search(
            [('id', 'in', company_ids)], limit=1)

    type = fields.Char('Check Type')
    state = fields.Char('Check State')
    reject_date = fields.Date(
        'Reject Date',
        required=True,
        default=fields.Date.context_today)
    expense_account = fields.Many2one(
        'account.account',
        'Expense Account',
        domain=[('type', 'in', ['other'])],)
    has_expense = fields.Boolean('Has Expense',
                                 default=True)
    expense_amount = fields.Float(
        'Expense Amount')
    expense_to_customer = fields.Boolean(
        'Invoice Expenses to Customer')
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=_get_company_id)

    def action_dreject(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_ids = context.get('active_ids', [])
        check_obj = self.pool.get('account.check')
        wizard = self.browse(cr, uid, ids[0], context=context)
        context['company_id'] = wizard.company_id.id

        # used to get correct ir properties
        context['force_company'] = wizard.company_id.id

        for check in check_obj.browse(cr, uid, record_ids, context=context):
            if check.state not in ['deposited', 'handed']:
                raise Warning(
                    _('Only deposited or handed checks can be rejected.'))

            if check.type == 'third':
                customer_invoice_id = self.make_invoice(
                    cr, uid, 'out_invoice', check, wizard, context=context)
                if wizard.has_expense and wizard.expense_to_customer:
                    self.make_expense_invoice_line(
                        cr, uid, customer_invoice_id, check, wizard,
                        context=context)
                elif wizard.has_expense:
                    self.make_expenses_move(
                        cr, uid, check, wizard, context=context)

            if check.state == 'handed':
                supplier_invoice_id = self.make_invoice(
                    cr, uid, 'in_invoice', check, wizard, context=context)
                if wizard.has_expense:
                    self.make_expense_invoice_line(
                        cr, uid, supplier_invoice_id, check, wizard,
                        context=context)
            check.signal_workflow('rejected')

    def make_expense_invoice_line(self, cr, uid, invoice_id, check, wizard, context=None):
        invoice_line_obj = self.pool.get('account.invoice.line')
        name = _('Rejected Expenses, Check N: ') + check.name
        invoice_line_obj.create(cr, uid, {
            'name': name,
            'origin': name,
            'invoice_id': invoice_id,
            'account_id': wizard.expense_account.id,
            'price_unit': wizard.expense_amount,
            'quantity': 1,
        }, context=context)

    def make_invoice(self, cr, uid, invoice_type, check, wizard, context=None):

        if not context:
            context = {}
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        journal_obj = self.pool.get('account.journal')
        if invoice_type == 'in_invoice':
            debit_note_field = 'supplier_reject_debit_note_id'
            journal_ids = journal_obj.search(cr, uid, [
                ('company_id', '=', wizard.company_id.id),
                ('type', '=', 'purchase')], context=context)
            partner_id = check.destiny_partner_id.id
            partner_account_id = check.voucher_id.partner_id.property_account_payable.id
            account_id = check.voucher_id.journal_id.default_credit_account_id.id
        else:
            debit_note_field = 'customer_reject_debit_note_id'
            journal_ids = journal_obj.search(cr, uid, [
                ('company_id', '=', wizard.company_id.id),
                ('type', '=', 'sale')], context=context)
            partner_account_id = check.voucher_id.partner_id.property_account_receivable.id
            partner_id = check.voucher_id.partner_id.id
            if check.state == 'handed':
                account_id = check.voucher_id.journal_id.default_credit_account_id.id
            else:
                account_id = check.deposit_account_id.id

        if not journal_ids:
            raise Warning(_('No journal for rejection in company %s') %
                          (wizard.company_id.name))
        else:
            journal_id = journal_ids[0]
        name = _('Check Rejected N: ')
        name += check.name
        invoice_vals = {
            'name': name,
            'origin': name,
            'type': invoice_type,
            'account_id': partner_account_id,
            'partner_id': partner_id,
            'date_invoice': wizard.reject_date,
            'company_id': wizard.company_id.id,
            'journal_id': journal_id,
        }
        invoice_id = invoice_obj.create(
            cr, uid, invoice_vals,
            context={'document_type': 'debit_note'})
        check.write({debit_note_field: invoice_id})

        invoice_line_vals = {
            'name': name,
            'origin': name,
            'invoice_id': invoice_id,
            'account_id': account_id,
            'price_unit': check.amount,
            'quantity': 1,
        }

        invoice_line_obj.create(cr, uid, invoice_line_vals)

        return invoice_id

    def make_expenses_move(self, cr, uid, check, wizard, context=None):
        move_line_obj = self.pool.get('account.move.line')
        period_id = self.pool.get('account.period').find(
            cr, uid, wizard.reject_date, context=context)[0]
        name = self.pool.get('ir.sequence').next_by_id(
            cr, uid, check.voucher_id.journal_id.sequence_id.id, context=context)
        ref = _('Check Rejected N: ')
        ref += check.name
        move_id = self.pool.get('account.move').create(cr, uid, {
            'name': name,
            'journal_id': check.voucher_id.journal_id.id,
            'period_id': period_id,
            'date': wizard.reject_date,
            'ref': _('Rejected Check Nr. ') + check.name,
        })

        move_line_obj.create(cr, uid, {
            'name': name,
            'centralisation': 'normal',
            'account_id': wizard.expense_account.id,
            'move_id': move_id,
            'period_id': period_id,
            'debit': wizard.expense_amount,
            'ref': ref,
        })

        if check.state == 'handed':
            account_id = check.voucher_id.journal_id.default_credit_account_id.id
        else:
            account_id = check.deposit_account_id.id
        move_line_obj.create(cr, uid, {
            'name': name,
            'centralisation': 'normal',
            'account_id': account_id,
            'move_id': move_id,
            'period_id': period_id,
            'credit': wizard.expense_amount,
            'ref': ref,
        })
        self.pool.get('account.move').write(cr, uid, [move_id], {
            'state': 'posted',
        })
        check.write({'expense_account_move_id': move_id})
