# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2012 Camptocamp SA
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
import logging
import pooler

from openerp.osv.orm import Model, fields

logger = logging.getLogger('credit.line.control')


class CreditControlLine(Model):
    """A credit control line describes an amount due by a customer for a due date.

    A line is created once the due date of the payment is exceeded.
    It is created in "draft" and some actions are available (send by email,
    print, ...)
    """

    _name = "credit.control.line"
    _description = "A credit control line"
    _rec_name = "id"

    _columns = {
        'date': fields.date('Controlling date', required=True),
        # maturity date of related move line we do not use a related field in order to
        # allow manual changes
        'date_due': fields.date('Due date',
                                required=True,
                                readonly=True,
                                states={'draft': [('readonly', False)]}),

        'date_sent': fields.date('Sent date',
                                 readonly=True,
                                 states={'draft': [('readonly', False)]}),

        'state': fields.selection([('draft', 'Draft'),
                                   ('to_be_sent', 'Ready To Send'),
                                   ('sent', 'Done'),
                                   ('error', 'Error'),
                                   ('mail_error', 'Mailing Error')],
                                  'State', required=True, readonly=True),

        'canal': fields.selection([('manual', 'Manual'),
                                   ('mail', 'Mail')],
                                  'Canal', required=True,
                                  readonly=True,
                                  states={'draft': [('readonly', False)]}),

        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'partner_id': fields.many2one('res.partner', "Partner", required=True),
        'amount_due': fields.float('Due Amount Tax incl.', required=True, readonly=True),
        'balance_due': fields.float('Due balance', required=True, readonly=True),
        'mail_message_id': fields.many2one('mail.message', 'Sent mail', readonly=True),

        'move_line_id': fields.many2one('account.move.line', 'Move line',
                                        required=True, readonly=True),

        'account_id': fields.related('move_line_id', 'account_id', type='many2one',
                                     relation='account.account', string='Account',
                                     store=True, readonly=True),

        'currency_id': fields.related('move_line_id', 'currency_id', type='many2one',
                                      relation='res.currency', string='Currency',
                                      store=True, readonly=True),

        'company_id': fields.related('move_line_id', 'company_id', type='many2one',
                                     relation='res.company', string='Company',
                                     store=True, readonly=True),

        # we can allow a manual change of policy in draft state
        'policy_level_id':fields.many2one('credit.control.policy.level',
                                          'Overdue Level', required=True, readonly=True,
                                          states={'draft': [('readonly', False)]}),

        'policy_id': fields.related('policy_level_id',
                                    'policy_id',
                                    type='many2one',
                                    relation='credit.control.policy',
                                    string='Policy',
                                    store=True,
                                    readonly=True),

        'level': fields.related('policy_level_id',
                                'level',
                                type='integer',
                                relation='credit.control.policy',
                                string='Level',
                                store=True,
                                readonly=True),
    }


    _defaults = {'state': 'draft'}

    def _update_from_mv_line(self, cursor, uid, ids, mv_line_br, level,
                             controlling_date, context=None):
        """hook function to update line if required"""
        context =  context or {}
        return []

    def _prepare_from_move_line(self, cursor, uid, move_line,
                                level, controlling_date, context=None):
        """Create credit control line"""
        acc_line_obj = self.pool.get('account.move.line')
        if context is None:
            context = {}
        data = {}
        data['date'] = controlling_date
        data['date_due'] = move_line.date_maturity
        data['state'] = 'draft'
        data['canal'] = level.canal
        data['invoice_id'] = move_line.invoice_id.id if move_line.invoice_id else False
        data['partner_id'] = move_line.partner_id.id
        data['amount_due'] = (move_line.amount_currency or move_line.debit or
                              move_line.credit)
        data['balance_due'] = acc_line_obj._amount_residual_from_date(
                cursor, uid, move_line, controlling_date, context=context)
        data['policy_level_id'] = level.id
        data['company_id'] = move_line.company_id.id
        data['move_line_id'] = move_line.id
        return data

    def create_or_update_from_mv_lines(self, cursor, uid, ids, lines,
                                       level_id, controlling_date, context=None):
        """Create or update line base on levels"""
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        level_obj = self.pool.get('credit.control.policy.level')
        ml_obj = self.pool.get('account.move.line')
        level = level_obj.browse(cursor, uid, level_id, context)
        current_lvl = level.level
        debit_line_ids = []
        user = self.pool.get('res.users').browse(cursor, uid, uid)
        tolerance_base = user.company_id.credit_control_tolerance
        currency_ids = currency_obj.search(cursor, uid, [], context=context)

        tolerance = {}
        acc_line_obj = self.pool.get('account.move.line')
        for c_id in currency_ids:
            tolerance[c_id] = currency_obj.compute(
                cursor, uid,
                c_id,
                user.company_id.currency_id.id,
                tolerance_base,
                context=context)

        existings = self.search(
            cursor, uid,
            [('move_line_id', 'in', lines),
             ('level', '=', current_lvl)],
            context=context)

        errors = []
        db = pooler.get_db(cursor.dbname)
        local_cr = db.cursor()
        try:
            for line in ml_obj.browse(cursor, uid, lines, context):
                # we want to create as many line as possible
                try:
                    if line.id in existings:
                        # does nothing just a hook
                        debit_line_ids += self._update_from_mv_line(
                            local_cr, uid, ids, line, level,
                            controlling_date, context=context)
                    else:
                        # as we use memoizer pattern this has almost no cost to get it
                        # multiple time
                        open_amount = acc_line_obj._amount_residual_from_date(
                            cursor, uid, line, controlling_date, context=context)

                        if open_amount > tolerance.get(line.currency_id.id, tolerance_base):
                            vals = self._prepare_from_move_line(
                                local_cr, uid, line, level, controlling_date, context=context)
                            debit_line_ids.append(self.create(local_cr, uid, vals, context=context))
                # FIXME: which exception can happens here ? reduce the exception scope
                except Exception, exc:
                    logger.exception(exc)
                    if errors:
                        errors.append(unicode(exc))
                    local_cr.rollback()
                finally:
                    local_cr.commit()
        finally:
            local_cr.close()
        return debit_line_ids, errors

