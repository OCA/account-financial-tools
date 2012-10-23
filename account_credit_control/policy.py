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
from openerp.osv.orm import Model, fields
from openerp.tools.translate import _


class CreditControlPolicy(Model):
    """Define a policy of reminder"""

    _name = "credit.control.policy"
    _description = """Define a reminder policy"""
    _columns = {'name': fields.char('Name', required=True, size=128),

                'level_ids' : fields.one2many('credit.control.policy.level',
                                                     'policy_id',
                                                     'Policy Levels'),

                'do_nothing' : fields.boolean('Do nothing',
                                              help=('For policies which should not '
                                                    'generate lines or are obsolete')),

                'company_id' : fields.many2one('res.company', 'Company')
                }


    def _get_account_related_lines(self, cursor, uid, policy_id, controlling_date, context=None):
        """ Get the move lines for a policy.

        Do not use direct SQL in order to respect security rules.

        Assume that only the receivable lines have a maturity date and that
        accounts used in the policy are reconcilable.
        """
        if context is None:
            context = {}
        move_l_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        acc_ids =  account_obj.search(
            cursor, uid, [('credit_policy_id', '=', policy_id)], context=context)
        if not acc_ids:
            return []
        lines = move_l_obj.search(cursor, uid,
                                  [('account_id', 'in', acc_ids),
                                   ('date_maturity', '<=', controlling_date),
                                   ('reconcile_id', '=', False),
                                   ('partner_id', '!=', False)],
                                  context=context)

        return lines

    def _get_sum_reduce_range(self, cursor, uid, policy_id, controlling_date, lines,
                              model, move_relation_field, context=None):
        """ Get the move lines related to one model for a policy.

            Do not use direct SQL in order to respect security rules.

            Assume that only the receivable lines have a maturity date and that
            accounts used in the policy are reconcilable.

            The policy relation field MUST be named credit_policy_id

            Warning: side effect on ``lines``

            """
        # MARK possible place for a good optimisation
        if context is None:
            context = {}
        my_obj = self.pool.get(model)
        move_l_obj = self.pool.get('account.move.line')
        add_lines = []
        neg_lines = []
        add_obj_ids = my_obj.search(
            cursor, uid, [('credit_policy_id', '=', policy_id)], context=context)
        if add_obj_ids:
            add_lines = move_l_obj.search(
                cursor, uid,
                [(move_relation_field, 'in', add_obj_ids),
                 ('date_maturity', '<=', controlling_date),
                 ('partner_id', '!=', False),
                 ('reconcile_id', '=', False)],
                context=context)
            lines = list(set(lines + add_lines))

        # we get all the lines that must be excluded at partner_level
        # from the global set (even the one included at account level)
        neg_obj_ids = my_obj.search(
            cursor, uid,
            [('credit_policy_id', '!=', policy_id),
             ('credit_policy_id', '!=', False)],
            context=context)
        if neg_obj_ids:
            # should we add ('id', 'in', lines) in domain ? it may give a veeery long SQL...
            neg_lines = move_l_obj.search(
                    cursor, uid,
                    [(move_relation_field, 'in', neg_obj_ids),
                     ('date_maturity', '<=', controlling_date),
                     ('partner_id', '!=', False),
                     ('reconcile_id', '=', False)],
                    context=context)
            if neg_lines:
                lines = list(set(lines) - set(neg_lines))
        return lines

    def _get_partner_related_lines(self, cursor, uid, policy_id, controlling_date, lines, context=None):
        """ Get the move lines for a policy related to a partner.
            Warning: side effect on ``lines``
        """
        return self._get_sum_reduce_range(cursor, uid, policy_id, controlling_date, lines,
                                          'res.partner', 'partner_id', context=context)

    def _get_invoice_related_lines(self, cursor, uid, policy_id, controlling_date, lines, context=None):
        """ Get the move lines for a policy related to an invoice.
            Warning: side effect on ``lines``
        """
        return self._get_sum_reduce_range(cursor, uid, policy_id, controlling_date, lines,
                                          'account.invoice', 'invoice', context=context)

    def _get_moves_line_to_process(self, cursor, uid, policy_id, controlling_date, context=None):
        """Retrive all the move line to be procces for current policy.
           This function is planned to be use only on one id.
           Priority of inclustion, exlusion is account, partner, invoice"""
        if context is None:
            context = {}
        lines = []
        assert not (isinstance(policy_id, list) and len(policy_id) > 1), \
            "policy_id: only one id expected"
        if isinstance(policy_id, list):
            policy_id = policy_id[0]
        # there is a priority between the lines, depicted by the calls below
        lines += self._get_account_related_lines(
                cursor, uid, policy_id, controlling_date, context=context)
        # warning, side effect method called on lines
        lines = self._get_partner_related_lines(
                cursor, uid, policy_id, controlling_date, lines, context=context)
        lines = self._get_invoice_related_lines(
                cursor, uid, policy_id, controlling_date, lines, context=context)
        return lines

    def _check_lines_policies(self, cursor, uid, policy_id, lines, context=None):
        """ Check if there is credit line related to same move line but
            related to an other policy"""
        if context is None:
            context = {}
        if not lines:
            return []
        assert not (isinstance(policy_id, list) and len(policy_id) > 1), \
            "policy_id: only one id expected"
        if isinstance(policy_id, list):
            policy_id = policy_id[0]
        cursor.execute("SELECT move_line_id FROM credit_control_line"
                       " WHERE policy_id != %s and move_line_id in %s",
                       (policy_id, tuple(lines)))
        res = cursor.fetchall()
        if res:
            return [x[0] for x in res]
        else:
            return []


class CreditControlPolicyLevel(Model):
    """Define a policy level. A level allows to determine if
    a move line is due and the level of overdue of the line"""

    _name = "credit.control.policy.level"
    _order = 'level'
    _description = """A credit control policy level"""
    _columns = {
        'policy_id': fields.many2one('credit.control.policy',
                                     'Related Policy', required=True),
        'name': fields.char('Name', size=128, required=True),
        'level': fields.integer('Level', required=True),

        'computation_mode': fields.selection([('net_days', 'Due Date'),
                                              ('end_of_month', 'Due Date, End Of Month'),
                                              ('previous_date', 'Previous Reminder')],
                                             'Compute Mode',
                                             required=True),

        'delay_days': fields.integer('Delay (in days)', required='True'),
        'mail_template_id': fields.many2one('email.template', 'Mail Template',
                                            required=True),
        'canal': fields.selection([('manual', 'Manual'),
                                   ('mail', 'Mail')],
                                  'Canal', required=True),
        'custom_text': fields.text('Custom Message', required=True, translate=True),
    }

    def _check_level_mode(self, cursor, uid, rids, context=None):
        """ The smallest level of a policy cannot be computed on the
        "previous_date". Return False if this happens.  """
        if isinstance(rids, (int, long)):
            rids = [rids]
        for level in self.browse(cursor, uid, rids, context):
            smallest_level_id = self.search(
                cursor, uid,
                [('policy_id', '=', level.policy_id.id)],
                order='level asc', limit=1, context=context)
            smallest_level = self.browse(cursor, uid, smallest_level_id[0], context)
            if smallest_level.computation_mode == 'previous_date':
                return False
        return True

    _sql_constraint = [('unique level',
                        'UNIQUE (policy_id, level)',
                        'Level must be unique per policy')]

    _constraints = [(_check_level_mode,
                     'The smallest level can not be of type Previous Reminder',
                     ['level'])]

    def _previous_level(self, cursor, uid, policy_level, context=None):
        """ For one policy level, returns the id of the previous level

        If there is no previous level, it returns None, it means that's the
        first policy level

        :param browse_record policy_level: policy level
        :return: previous level id or None if there is no previous level
        """
        previous_level_ids = self.search(
            cursor,
            uid,
            [('policy_id', '=', policy_level.policy_id.id),
             ('level', '<', policy_level.level)],
            order='level desc',
            limit=1,
            context=context)
        return previous_level_ids[0] if previous_level_ids else None

    # ----- sql time related methods ---------

    def _net_days_get_boundary(self):
        return " (mv_line.date_maturity + %(delay)s)::date <= date(%(controlling_date)s)"

    def _end_of_month_get_boundary(self):
        return ("(date_trunc('MONTH', (mv_line.date_maturity + %(delay)s))+INTERVAL '1 MONTH - 1 day')::date"
                "<= date(%(controlling_date)s)")

    def _previous_date_get_boundary(self):
        return "(cr_line.date + %(delay)s)::date <= date(%(controlling_date)s)"

    def _get_sql_date_boundary_for_computation_mode(self, cursor, uid, level, controlling_date, context=None):
        """Return a where clauses statement for the given
           controlling date and computation mode of the level"""
        fname = "_%s_get_boundary" % (level.computation_mode,)
        if hasattr(self, fname):
            fnc = getattr(self, fname)
            return fnc()
        else:
            raise NotImplementedError(_('Can not get function for computation mode: '
                                        '%s is not implemented') % (fname,))

    # -----------------------------------------

    def _get_first_level_lines(self, cursor, uid, level, controlling_date, lines, context=None):
        if not lines:
            return []
        """Retrieve all the move lines that are linked to a first level.
           We use Raw SQL for performance. Security rule where applied in
           policy object when the first set of lines were retrieved"""
        sql = ("SELECT DISTINCT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " WHERE mv_line.id in %(line_ids)s\n"
               " AND NOT EXISTS (SELECT cr_line.id from credit_control_line cr_line\n"
               "                  WHERE cr_line.move_line_id = mv_line.id)")
        sql += " AND" + self._get_sql_date_boundary_for_computation_mode(
                cursor, uid, level, controlling_date, context)
        data_dict = {'controlling_date': controlling_date, 'line_ids': tuple(lines),
                     'delay': level.delay_days}

        cursor.execute(sql, data_dict)
        res = cursor.fetchall()
        if not res:
            return []
        return [x[0] for x in res]

    def _get_other_level_lines(self, cursor, uid, level, controlling_date, lines, context=None):
        """ Retrieve the move lines for other levels than first level.
        """
        if not lines:
            return []
        sql = ("SELECT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " JOIN  credit_control_line cr_line\n"
               " ON (mv_line.id = cr_line.move_line_id)\n"
               " WHERE cr_line.id = (SELECT credit_control_line.id FROM credit_control_line\n"
               "                            WHERE credit_control_line.move_line_id = mv_line.id\n"
               "                              ORDER BY credit_control_line.level desc limit 1)\n"
               " AND cr_line.level = %(level)s\n"
               " AND mv_line.id in %(line_ids)s\n")
        sql += " AND " + self._get_sql_date_boundary_for_computation_mode(
                cursor, uid, level, controlling_date, context)
        previous_level_id = self._previous_level(
                cursor, uid, level, context=context)
        previous_level = self.browse(
                cursor, uid, previous_level_id, context=context)
        data_dict =  {'controlling_date': controlling_date, 'line_ids': tuple(lines),
                     'delay': level.delay_days, 'level': previous_level.level}

        cursor.execute(sql, data_dict)
        res = cursor.fetchall()
        if not res:
            return []
        return [x[0] for x in res]

    def get_level_lines(self, cursor, uid, level_id, controlling_date, lines, context=None):
        """get all move lines in entry lines that match the current level"""
        assert not (isinstance(level_id, list) and len(level_id) > 1), "level_id: only one id expected"
        if isinstance(level_id, list):
            level_id = level_id[0]
        matching_lines = []
        level = self.browse(cursor, uid, level_id, context=context)
        if self._previous_level(cursor, uid, level, context=context) is None:
            matching_lines += self._get_first_level_lines(
                cursor, uid, level, controlling_date, lines, context=context)
        else:
            matching_lines += self._get_other_level_lines(
                cursor, uid, level, controlling_date, lines, context=context)

        return matching_lines

