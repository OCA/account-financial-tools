# -*- coding: utf-8 -*-


from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


#----------------------------------------------------------
# Accounts
#----------------------------------------------------------


class AccountAccount(models.Model):
    _inherit = "account.account"



    @api.multi
    def write(self, vals):
        accounts = []
        aml = self.env['account.move.line']
        for account in self:
            if vals.get('reconcile') \
                     and not account.reconcile \
                     and not len(aml.search([('account_id','=', account.id),('reconciled','=', True)])) > 0\
                     and len(aml.search([('account_id','=', account.id)])) > 0:
                accounts.append(account.id)
                vals.pop('reconcile')
            elif vals.get('reconcile') == False:
                move_lines = self.env['account.move.line'].search([('account_id', 'in', self.ids)], limit=1)
                if len(move_lines):
                    raise UserError(_('You cannot switch reconciliation off on this account as it already has some moves'))
        if accounts != []:
            self.set_reconcile_true(accounts)
        return super(AccountAccount, self).write(vals)

    @api.multi
    def set_reconcile_true(self, ids):
        for account in self.env['account.account'].search([('id','in',ids)]):
            if account.reconcile:
                raise UserError(_('You are trying to switch on reconciliation on %s %s %s, that already has reconcile True') %
                                (account.code, account.name, account.company_id.name))
        str_lst = ','.join([str(item) for item in ids])

        # UPDATE query to compute residual amounts
        sql_aml = ("""UPDATE account_move_line
                    SET 
                    reconciled = false,
                    amount_residual = debit - credit,
                    amount_residual_currency = CASE 
                                                WHEN amount_currency > 0 
                                                AND currency_id IS NOT NULL 
                                                THEN amount_currency 
                                                ELSE 0 
                                               END
                    {0};""".format(
                    "WHERE account_id in (%s)" % str_lst
                    ))
        self.env.cr.execute(sql_aml)

        # UPDATE query to set reconcile = true in account_account
        sql_account = ("""UPDATE account_account
                    SET 
                    reconcile = true
                    {0};""".format(
                    "WHERE id in (%s)" % str_lst
                    ))
        self.env.cr.execute(sql_account)