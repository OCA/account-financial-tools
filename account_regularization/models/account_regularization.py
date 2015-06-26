# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#    All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 Acysos SL. All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields
import time


class AccountAccount(models.Model):
    _name = 'account.account'
    _inherit = 'account.account'

    @api.multi
    def balance_calculation(self, date=time.strftime('%Y-%m-%d'), periods=[]):
        acc_set = ",".join(map(str, self.ids))
        query = self.env['account.move.line']._query_get()

        if not periods:
            self.env.cr.execute(("SELECT a.id, "
                                 "COALESCE(SUM(l.debit - l.credit), 0) "
                                 "FROM account_account a "
                                 "LEFT JOIN account_move_line l "
                                 "ON (a.id=l.account_id) "
                                 "WHERE a.type != 'view' "
                                 "AND a.id IN (%s) "
                                 "AND " + query + " "
                                 "AND a.active "
                                 "AND l.date <= '%s' "
                                 "GROUP BY a.id") % (acc_set, date))
        else:
            period_ids = ",".join(str(period.id) for period in periods)
            self.env.cr.execute(("SELECT a.id, "
                                 "COALESCE(SUM(l.debit - l.credit), 0) "
                                 "FROM account_account a "
                                 "LEFT JOIN account_move_line l "
                                 "ON (a.id=l.account_id) "
                                 "WHERE a.type != 'view' "
                                 "AND a.id IN (%s) "
                                 "AND " + query + " "
                                 "AND a.active "
                                 "AND l.period_id in (%s) "
                                 "GROUP BY a.id") % (acc_set, period_ids))

        res = {}
        for account_id, sum in self.env.cr.fetchall():
            res[account_id] = round(sum, 2)
        for id in self.ids:
            res[id] = round(res.get(id, 0.0), 2)
        return res


class AccountRegularization(models.Model):
    _name = 'account.regularization'
    _description = 'Account Regularization Model'

    name = fields.Char('Name', size=32, required=True)
    account_ids = fields.Many2many('account.account',
                                   'account_regularization_rel',
                                   'regularization_id',
                                   'account_id', 'Accounts to balance',
                                   required=True,
                                   domain=[('type', '=', 'view')])
    debit_account_id = fields.Many2one('account.account',
                                       'Result account,'
                                       ' debit',
                                       required=True)
    credit_account_id = fields.Many2one('account.account',
                                        'Result account,'
                                        ' credit',
                                        required=True)
    balance_calc = fields.Selection([('date', 'Date'),
                                     ('period', 'Periods')],
                                    'Regularization time calculation',
                                    required=True, default='period')

    move_ids = fields.One2many('account.move',
                               'regularization_id',
                               'Regularization Moves')

    @api.one
    def regularize(self, date=time.strftime('%Y-%m-%d'),
                   period=None, journal=None, date_to=None,
                   period_ids=[]):
        """ This method will calculate all the balances from all
        the child accounts of the regularization
        and create the corresponding move."""
        #assert len(id) == 1, "One regularization at a time"
        if not period or not journal:
            raise Exception('No period or journal defined')
        #regularization = self.browse(cr, uid, id)[0]
        # Find all children accounts
        account_ids = [x.id for x in self.account_ids]
        tot_account_ids = self.env['account.account'].\
            browse(account_ids)._get_children_and_consol()
        if date_to:
            balance_results = self.env['account.account'].\
                browse(tot_account_ids).balance_calculation(date=date_to)
        else:
            balance_results = self.env['account.account'].\
                browse(tot_account_ids).balance_calculation(periods=period_ids)
        if balance_results.keys().__len__() ==\
                balance_results.values().count(0.0):
            raise Exception('Nothing to regularize',
                            'Nothing to regularize')
        move = self.env['account.move'].create(
            {'journal_id': journal.id,
             'period_id': period.id,
             'regularization_id': self.id})
        sum = 0.0
        for item in balance_results.keys():
            if balance_results[item] != 0.0:
                val = {
                    'name': self.name,
                    'date': date,
                    'move_id': move.id,
                    'account_id': item,
                    'credit': ((balance_results[item] > 0.0)
                               and balance_results[item]) or 0.0,
                    'debit': ((balance_results[item] < 0.0)
                              and -balance_results[item]) or 0.0,
                    'journal_id': journal.id,
                    'period_id': period.id,
                }
                sum += balance_results[item]
                self.env['account.move.line'].create(val)
        diff_line = {
            'name': self.name,
            'date': date,
            'move_id': move.id,
            'account_id': (sum > 0) and
            self.debit_account_id.id or
            self.credit_account_id.id,
            'credit': ((sum < 0.0) and -sum) or 0.0,
            'debit': ((sum > 0.0) and sum) or 0.0,
            'journal_id': journal.id,
            'period_id': period.id,
        }
        self.env['account.move.line'].create(diff_line)
        return


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = 'account.move'

    regularization_id = fields.Many2one('account.regularization',
                                        'Regularization')
