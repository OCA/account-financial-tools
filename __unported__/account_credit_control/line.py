# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
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

from openerp.osv import orm, fields
from openerp.tools.translate import _

logger = logging.getLogger('credit.line.control')


class CreditControlLine(orm.Model):
    """A credit control line describes an amount due by a customer for a due date.

    A line is created once the due date of the payment is exceeded.
    It is created in "draft" and some actions are available (send by email,
    print, ...)
    """

    _name = "credit.control.line"
    _description = "A credit control line"
    _rec_name = "id"
    _order = "date DESC"
    _columns = {
        'date': fields.date(
            'Controlling date',
            required=True,
            select=True
        ),
        # maturity date of related move line we do not use a related field in order to
        # allow manual changes
        'date_due': fields.date(
            'Due date',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}
        ),

        'date_entry': fields.related(
            'move_line_id', 'date',
            type='date',
            string='Entry date',
            store=True, readonly=True
        ),

        'date_sent': fields.date(
            'Sent date',
            readonly=True,
            states={'draft': [('readonly', False)]}
        ),

        'state': fields.selection(
            [('draft', 'Draft'),
             ('ignored', 'Ignored'),
             ('to_be_sent', 'Ready To Send'),
             ('sent', 'Done'),
             ('error', 'Error'),
             ('email_error', 'Emailing Error')],
            'State', required=True, readonly=True,
            help=("Draft lines need to be triaged.\n"
                  "Ignored lines are lines for which we do "
                  "not want to send something.\n"
                  "Draft and ignored lines will be "
                  "generated again on the next run.")
        ),

        'channel': fields.selection(
            [('letter', 'Letter'),
             ('email', 'Email')],
            'Channel', required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}
        ),

        'invoice_id': fields.many2one(
            'account.invoice',
            'Invoice',
            readonly=True
        ),

        'partner_id': fields.many2one(
            'res.partner',
            "Partner",
            required=True
        ),

        'amount_due': fields.float(
            'Due Amount Tax incl.',
            required=True,
            readonly=True
        ),

        'balance_due': fields.float(
            'Due balance', required=True,
            readonly=True
        ),

        'mail_message_id': fields.many2one(
            'mail.mail',
            'Sent Email',
            readonly=True
        ),

        'move_line_id': fields.many2one(
            'account.move.line',
            'Move line',
            required=True,
            readonly=True
        ),

        'account_id': fields.related(
            'move_line_id',
            'account_id',
            type='many2one',
            relation='account.account',
            string='Account',
            store=True,
            readonly=True
        ),

        'currency_id': fields.related(
            'move_line_id',
            'currency_id',
            type='many2one',
            relation='res.currency',
            string='Currency',
            store=True,
            readonly=True
        ),

        'company_id': fields.related(
            'move_line_id', 'company_id',
            type='many2one',
            relation='res.company',
            string='Company',
            store=True, readonly=True
        ),

        # we can allow a manual change of policy in draft state
        'policy_level_id': fields.many2one(
            'credit.control.policy.level',
            'Overdue Level',
            required=True,
            readonly=True,
            states={'draft': [('readonly', False)]}
        ),

        'policy_id': fields.related(
            'policy_level_id',
            'policy_id',
            type='many2one',
            relation='credit.control.policy',
            string='Policy',
            store=True,
            readonly=True
        ),

        'level': fields.related(
            'policy_level_id',
            'level',
            type='integer',
            relation='credit.control.policy',
            string='Level',
            store=True,
            readonly=True
        ),

        'manually_overridden': fields.boolean('Manually overridden')
    }

    _defaults = {'state': 'draft'}

    def _prepare_from_move_line(self, cr, uid, move_line,
                                level, controlling_date, open_amount,
                                context=None):
        """Create credit control line"""
        data = {}
        data['date'] = controlling_date
        data['date_due'] = move_line.date_maturity
        data['state'] = 'draft'
        data['channel'] = level.channel
        data['invoice_id'] = move_line.invoice.id if move_line.invoice else False
        data['partner_id'] = move_line.partner_id.id
        data['amount_due'] = (move_line.amount_currency or move_line.debit or
                              move_line.credit)
        data['balance_due'] = open_amount
        data['policy_level_id'] = level.id
        data['company_id'] = move_line.company_id.id
        data['move_line_id'] = move_line.id
        return data

    def create_or_update_from_mv_lines(self, cr, uid, ids, lines,
                                       level_id, controlling_date,
                                       check_tolerance=True, context=None):
        """Create or update line based on levels

        if check_tolerance is true credit line will not be
        created if open amount is too small.
        eg. we do not want to send a letter for 10 cents
        of open amount.

        :param lines: move.line id list
        :param level_id: credit.control.policy.level id
        :param controlling_date: date string of the credit controlling date.
                                 Generally it should be the same
                                 as create date
        :param check_tolerance: boolean if True credit line
                                will not be generated if open amount
                                is smaller than company defined
                                tolerance

        :returns: list of created credit line ids
        """
        currency_obj = self.pool.get('res.currency')
        level_obj = self.pool.get('credit.control.policy.level')
        ml_obj = self.pool.get('account.move.line')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        currency_ids = currency_obj.search(cr, uid, [], context=context)

        tolerance = {}
        tolerance_base = user.company_id.credit_control_tolerance
        for c_id in currency_ids:
            tolerance[c_id] = currency_obj.compute(
                cr, uid,
                c_id,
                user.company_id.currency_id.id,
                tolerance_base,
                context=context)

        level = level_obj.browse(cr, uid, level_id, context)
        line_ids = []
        for line in ml_obj.browse(cr, uid, lines, context):

            open_amount = line.amount_residual_currency
            cur_tolerance = tolerance.get(line.currency_id.id, tolerance_base)
            if check_tolerance and open_amount < cur_tolerance:
                continue
            vals = self._prepare_from_move_line(cr, uid,
                                                line,
                                                level,
                                                controlling_date,
                                                open_amount,
                                                context=context)
            line_id = self.create(cr, uid, vals, context=context)
            line_ids.append(line_id)

            # when we have lines generated earlier in draft,
            # on the same level, it means that we have left
            # them, so they are to be considered as ignored
            previous_draft_ids = self.search(
                cr, uid,
                [('move_line_id', '=', line.id),
                 ('policy_level_id', '=', level.id),
                 ('state', '=', 'draft'),
                 ('id', '!=', line_id)],
                context=context)
            if previous_draft_ids:
                self.write(cr, uid, previous_draft_ids,
                           {'state': 'ignored'}, context=context)

        return line_ids

    def unlink(self, cr, uid, ids, context=None, check=True):
        for line in self.browse(cr, uid, ids, context=context):
            if line.state != 'draft':
                raise orm.except_orm(
                    _('Error !'),
                    _('You are not allowed to delete a credit control line that '
                      'is not in draft state.'))

        return super(CreditControlLine, self).unlink(cr, uid, ids, context=context)
