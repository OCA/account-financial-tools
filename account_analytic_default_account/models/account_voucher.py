# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Damien Crier
#    Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import api, models


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    @api.model
    def writeoff_move_line_get(self, voucher_id, line_total, move_id, name,
                               company_currency, current_currency):
        """

        """
        move_line = super(account_voucher, self).writeoff_move_line_get(
            voucher_id, line_total, move_id, name,
            company_currency, current_currency)
        if move_line:
            acc_bk_st_line_obj = self.env['account.bank.statement.line']
            if 'analytic_account_id' in move_line:
                if not move_line.get('analytic_account_id', False):
                    # so add one with the value of the analytic account
                    # corresponding to the account defined in the dictionnary
                    move_line['analytic_account_id'] = (
                        acc_bk_st_line_obj.get_default_analytic_account_id(
                            move_line['account_id'])
                        )

                else:
                    # a value already exists in the dictionnary so do not
                    # modify this one
                    pass
            else:
                # no key in the dictionnary, so add one with the
                # value of the analytic account corresponding to
                # the account defined in the dictionnary
                move_line['analytic_account_id'] = (
                    acc_bk_st_line_obj.get_default_analytic_account_id(
                        move_line['account_id'])
                    )

        return move_line

    @api.multi
    def onchange_writeoff_acc_id(self, writeoff_acc_id):
        res = {}
        if writeoff_acc_id:
            acc_bk_st_line_obj = self.env['account.bank.statement.line']
            analytic_acc_id = (
                acc_bk_st_line_obj.get_default_analytic_account_id(
                    writeoff_acc_id)
                )
            if analytic_acc_id:
                res['value'] = {'analytic_id': analytic_acc_id}

        return res

    @api.model
    def _get_exchange_lines(self, line, move_id, amount_residual,
                            company_currency, current_currency):
        '''
        '''
        acc_bk_st_line_obj = self.env['account.bank.statement.line']
        move_line, move_line_counterpart = (
            super(account_voucher, self)._get_exchange_lines(
                line,
                move_id,
                amount_residual,
                company_currency,
                current_currency
                )
            )

        move_line_counterpart_analytic_acc_id = (
            acc_bk_st_line_obj.get_default_analytic_account_id(
                move_line_counterpart['account_id'])
            )
        move_line_analytic_acc_id = (
            acc_bk_st_line_obj.get_default_analytic_account_id(
                move_line['account_id'])
            )

        if 'analytic_account_id' in move_line_counterpart:
            if not move_line_counterpart.get('analytic_account_id', False):
                move_line_counterpart['analytic_account_id'] = (
                    move_line_counterpart_analytic_acc_id
                    )

        else:
            move_line_counterpart['analytic_account_id'] = (
                move_line_counterpart_analytic_acc_id
                )

        if 'analytic_account_id' in move_line:
            if not move_line.get('analytic_account_id', False):
                move_line['analytic_account_id'] = move_line_analytic_acc_id

        else:
            move_line['analytic_account_id'] = move_line_analytic_acc_id

        return (move_line, move_line_counterpart)
