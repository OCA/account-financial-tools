# -*- coding: utf-8 -*-
##############################################################################
#
#    ODOO, Open Source Management Solution
#    Copyright (C) 2016 Steigend IT Solutions
#    For more details, check COPYRIGHT and LICENSE files
#
##############################################################################

import odoo.addons.decimal_precision as dp
from odoo import _, api, fields, models


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    type = fields.Selection(selection_add=[('view', 'View')])


class AccountAccount(models.Model):
    _inherit = "account.account"

    @api.model
    def _move_domain_get(self, domain=None):
        context = dict(self._context or {})
        domain = domain and safe_eval(str(domain)) or []

        res = ''
        date_field = 'date'
        if context.get('aged_balance'):
            date_field = 'date_maturity'
        if context.get('date_to'):
            res += " AND l.{} <= '{}' ".format(date_field, context['date_to'])
        if context.get('date_from'):
            if not context.get('strict_range'):
                res += " AND ({} >= '{}' OR at.include_initial_balance = true) ".format(
                    date_field, context['date_from'], )
            elif context.get('initial_bal'):
                res += " AND l.{} < '{}' ".format(date_field,
                                                  context['date_from'])
            else:
                res += " AND l.{} >= '{}' ".format(
                    date_field, context['date_from'])

        if context.get('journal_ids'):
            res += " AND l.journal_id in {} ".format(
                tuple(context['journal_ids']))

        state = context.get('state')
        if state and state.lower() != 'all':
            res += " AND m.state = '{}' ".format(state)

        if context.get('company_id'):
            res += " AND l.company_id = {} ".format(context['company_id'])

        if 'company_ids' in context:
            res += " AND l.company_id  in {} ".format(
                tuple(context['company_ids']))

        return res

    @api.multi
    @api.depends('move_line_ids', 'move_line_ids.amount_currency', 'move_line_ids.debit', 'move_line_ids.credit')
    def compute_values(self):
        default_domain = self._move_domain_get()
        query_tmpl = '''
            SELECT sum(debit) debit, sum(credit) credit, sum(debit - credit) balance
            FROM account_move_line l
            LEFT JOIN account_move m ON l.move_id = m.id
            LEFT JOIN account_account a ON l.account_id = a.id
            LEFT JOIN account_account_type at ON a.user_type_id = at.id
            WHERE 1 = 1 AND l.account_id in (%s)
        ''' + default_domain

        for account in self:
            sub_accounts = self.with_context(
                {'show_parent_account': True}).search([
                    ('id', 'child_of', [account.id])])
            query = query_tmpl % ','.join(map(str, tuple(sub_accounts.ids)))
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()[0]
            account.balance = result['balance']
            account.credit = result['credit']
            account.debit = result['debit']

    move_line_ids = fields.One2many(
        'account.move.line', 'account_id', 'Journal Entry Lines')
    balance = fields.Float(compute="compute_values",
                           digits=dp.get_precision('Account'), string='Balance')
    credit = fields.Float(compute="compute_values",
                          digits=dp.get_precision('Account'), string='Credit')
    debit = fields.Float(compute="compute_values",
                         digits=dp.get_precision('Account'), string='Debit')
    parent_id = fields.Many2one(
        'account.account', 'Parent Account', ondelete="set null")
    child_ids = fields.One2many(
        'account.account', 'parent_id', 'Child Accounts')
    parent_left = fields.Integer('Left Parent', index=1)
    parent_right = fields.Integer('Right Parent', index=1)

    _parent_name = "parent_id"
    _parent_store = True
    _parent_order = 'code, name'
    _order = 'parent_left'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        context = self._context or {}
        if not context.get('show_parent_account', False):
            args += [('user_type_id.type', '!=', 'view')]
        return super(AccountAccount, self).search(args, offset, limit, order, count=count)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    @api.model
    def _prepare_liquidity_account(self, name, company, currency_id, type):
        res = super(AccountJournal, self)._prepare_liquidity_account(
            name, company, currency_id, type)
        # Seek the next available number for the account code
        code_digits = company.accounts_code_digits or 0
        if type == 'bank':
            account_code_prefix = company.bank_account_code_prefix or ''
        else:
            account_code_prefix = company.cash_account_code_prefix or company.bank_account_code_prefix or ''

        liquidity_type = self.env.ref('account_parent.data_account_type_view')
        parent_id = self.env['account.account'].search([('code', '=', account_code_prefix),
                                                        ('company_id', '=', company.id), ('user_type_id', '=', liquidity_type.id)], limit=1)

        if parent_id:
            res.update({'parent_id': parent_id.id})
        return res
