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
            # we check if the write tries to set reconcile to true and there are move lines with this account, but not
            # yet reconciled, because then the computation becomes a lot more difficult. We fill the accounts list and
            # remove the "reconcile" key from the vals dict so it will not stumble upon the original write.
            if vals.get('reconcile') \
                     and not account.reconcile \
                     and not len(aml.search([('account_id','=', account.id),('reconciled','=', True)], limit=1)) \
                     and len(aml.search([('account_id','=', account.id)], limit=1)):
                accounts.append(account.id)
                vals.pop('reconcile')
            # in the case, that there are already reconciled lines, a user error is displayed
            elif vals.get('reconcile') \
                     and len(aml.search([('account_id', '=', account.id), ('reconciled', '=', True)], limit=1)):
                raise UserError(_('You cannot switch reconciliation on on this account as it already has reconciled moves'
                                  'it must have been switched off before. Now you will have to create a new account'))
            # not sure if this is still necessary. In the original write unsetting was allowed and we take care, that
            # with reconciled move lines but switched off, it cannot be set again. Maybe we should allow to unset it.
            elif vals.get('reconcile') == False \
                     and account.reconcile\
                     and len(self.env['account.move.line'].search([('account_id', '=', account.id),('reconciled','=', True)], limit=1)):
                raise UserError(_('You cannot switch reconciliation off on this account as it already has reconciled moves'))
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