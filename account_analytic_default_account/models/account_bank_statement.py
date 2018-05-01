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

from openerp import api, models, fields


class account_bank_statement_line(models.Model):
    _inherit = 'account.bank.statement.line'

    def get_default_analytic_account_id(self, account_id):
        """
        """
        acc_ana_def_obj = self.env['account.analytic.default']
        today = fields.Date.today()
        s_args = [
            ('account_id', '=', account_id),
            '|', ('date_start', '=', False), ('date_start', '>=', today),
            '|', ('date_stop', '=', False), ('date_stop', '<=', today)
        ]
        ana_def_rs = acc_ana_def_obj.search(s_args)
        if ana_def_rs:
            return ana_def_rs[0].analytic_id.id
        else:
            return False

    @api.model
    def get_currency_rate_line(self, st_line, currency_diff, move_id):
        """

        """
        res = super(account_bank_statement_line, self).get_currency_rate_line(
            st_line, currency_diff, move_id)

        if res:
            if 'account_analytic_id' in res:
                if not res.get('account_analytic_id', False):
                    # so add one with the value of the analytic account
                    # corresponding to the account defined in the dictionnary
                    res['analytic_account_id'] = (
                        self.get_default_analytic_account_id(
                            res['account_id'])
                        )

                else:
                    # a value already exists in the dictionnary so do not
                    # modify this one
                    pass

            else:
                # no key in the dictionnary, so add one with the
                # value of the analytic account corresponding to
                # the account defined in the dictionnary
                res['analytic_account_id'] = (
                    self.get_default_analytic_account_id(
                        res['account_id'])
                    )

        return res
