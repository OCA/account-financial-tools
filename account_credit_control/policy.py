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
from openerp.osv.orm import Model, fields
from openerp.tools.translate import _


class CreditControlPolicy(Model):
    """Define a policy of reminder"""

    _name = "credit.control.policy"
    _description = """Define a reminder policy"""
    _columns = {'name': fields.char('Name', required=True, size=128),

                'level_ids': fields.one2many('credit.control.policy.level',
                                                     'policy_id',
                                                     'Policy Levels'),

                'do_nothing': fields.boolean('Do nothing',
                                              help=('For policies which should not '
                                                    'generate lines or are obsolete')),

                'company_id': fields.many2one('res.company', 'Company'),

                'account_ids': fields.many2many(
                    'account.account',
                    string='Accounts',
                    required=True,
                    domain="[('reconcile', '=', True)]",
                    help='This policy will be active only for the selected accounts'),
                }

    def _move_lines_domain(self, cr, uid, policy, controlling_date, context=None):
        """Build the default domain for searching move lines"""
        account_ids = [a.id for a in policy.account_ids]
        return [('account_id', 'in', account_ids),
                ('date_maturity', '<=', controlling_date),
                ('reconcile_id', '=', False),
                ('partner_id', '!=', False)]

    def _due_move_lines(self, cr, uid, policy, controlling_date, context=None):
        """ Get the due move lines for the policy of the company.

        The set of ids will be reduced and extended according to the specific policies
        defined on partners and invoices.

        Do not use direct SQL in order to respect security rules.

        Assume that only the receivable lines have a maturity date and that
        accounts used in the policy are reconcilable.
        """
        move_l_obj = self.pool.get('account.move.line')
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id.credit_policy_id.id != policy.id:
            return set()

        return set(move_l_obj.search(
                cr, uid,
                self._move_lines_domain(cr, uid, policy, controlling_date, context=context),
                context=context))

    def _move_lines_subset(self, cr, uid, policy, controlling_date,
                          model, move_relation_field, context=None):
        """ Get the move lines related to one model for a policy.

        Do not use direct SQL in order to respect security rules.

        Assume that only the receivable lines have a maturity date and that
        accounts used in the policy are reconcilable.

        The policy relation field must be named credit_policy_id.

        :param browse_record policy: policy
        :param str controlling_date: date of credit control
        :param str model: name of the model where is defined a credit_policy_id
        :param str move_relation_field: name of the field in account.move.line
            which is a many2one to `model`
        :return: set of ids to add in the process, set of ids to remove from
            the process
        """
        # MARK possible place for a good optimisation
        my_obj = self.pool.get(model)
        move_l_obj = self.pool.get('account.move.line')

        default_domain = self._move_lines_domain(cr, uid, policy, controlling_date, context=context)
        to_add_ids = set()
        to_remove_ids = set()

        # The lines which are linked to this policy have to be included in the
        # run for this policy.
        # If another object override the credit_policy_id (ie. invoice after
        add_obj_ids = my_obj.search(
            cr, uid,
            [('credit_policy_id', '=', policy.id)],
            context=context)
        if add_obj_ids:
            domain = list(default_domain)
            domain.append((move_relation_field, 'in', add_obj_ids))
            to_add_ids = set(move_l_obj.search(cr, uid, domain, context=context))

        # The lines which are linked to another policy do not have to be
        # included in the run for this policy.
        neg_obj_ids = my_obj.search(
            cr, uid,
            [('credit_policy_id', '!=', policy.id),
             ('credit_policy_id', '!=', False)],
            context=context)
        if neg_obj_ids:
            domain = list(default_domain)
            domain.append((move_relation_field, 'in', neg_obj_ids))
            to_remove_ids = set(move_l_obj.search(cr, uid, domain, context=context))
        return to_add_ids, to_remove_ids

    def _get_partner_related_lines(self, cr, uid, policy, controlling_date, context=None):
        """ Get the move lines for a policy related to a partner.

        :param browse_record policy: policy
        :param str controlling_date: date of credit control
        :param str model: name of the model where is defined a credit_policy_id
        :param str move_relation_field: name of the field in account.move.line
            which is a many2one to `model`
        :return: set of ids to add in the process, set of ids to remove from
            the process
        """
        return self._move_lines_subset(
                cr, uid, policy, controlling_date,
                'res.partner', 'partner_id', context=context)

    def _get_invoice_related_lines(self, cr, uid, policy, controlling_date, context=None):
        """ Get the move lines for a policy related to an invoice.

        :param browse_record policy: policy
        :param str controlling_date: date of credit control
        :param str model: name of the model where is defined a credit_policy_id
        :param str move_relation_field: name of the field in account.move.line
            which is a many2one to `model`
        :return: set of ids to add in the process, set of ids to remove from
            the process
        """
        return self._move_lines_subset(
                cr, uid, policy, controlling_date,
                'account.invoice', 'invoice', context=context)

    def _get_move_lines_to_process(self, cr, uid, policy_id, controlling_date, context=None):
        """Build a list of move lines ids to include in a run for a policy at a given date.

        :param int/long policy: id of the policy
        :param str controlling_date: date of credit control
        :return: set of ids to include in the run
       """
        assert not (isinstance(policy_id, list) and len(policy_id) > 1), \
            "policy_id: only one id expected"
        if isinstance(policy_id, list):
            policy_id = policy_id[0]

        policy = self.browse(cr, uid, policy_id, context=context)
        # there is a priority between the lines, depicted by the calls below
        # warning, side effect method called on lines
        lines = self._due_move_lines(
                    cr, uid, policy, controlling_date, context=context)
        add_ids, remove_ids = self._get_partner_related_lines(
                    cr, uid, policy, controlling_date, context=context)
        lines = lines.union(add_ids).difference(remove_ids)
        add_ids, remove_ids = self._get_invoice_related_lines(
                    cr, uid, policy, controlling_date, context=context)
        lines = lines.union(add_ids).difference(remove_ids)
        return lines

    def _lines_different_policy(self, cr, uid, policy_id, lines, context=None):
        """ Return a set of move lines ids for which there is an existing credit line
            but with a different policy.
        """
        different_lines = set()
        if not lines:
            return different_lines
        assert not (isinstance(policy_id, list) and len(policy_id) > 1), \
            "policy_id: only one id expected"
        if isinstance(policy_id, list):
            policy_id = policy_id[0]
        cr.execute("SELECT move_line_id FROM credit_control_line"
                       " WHERE policy_id != %s and move_line_id in %s",
                       (policy_id, tuple(lines)))
        res = cr.fetchall()
        if res:
            different_lines.update([x[0] for x in res])
        return different_lines


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
        'email_template_id': fields.many2one('email.template', 'Email Template',
                                            required=True),
        'channel': fields.selection([('letter', 'Letter'),
                                   ('email', 'Email')],
                                  'Channel', required=True),
        'custom_text': fields.text('Custom Message', required=True, translate=True),
    }

    def _check_level_mode(self, cr, uid, rids, context=None):
        """ The smallest level of a policy cannot be computed on the
        "previous_date". Return False if this happens.  """
        if isinstance(rids, (int, long)):
            rids = [rids]
        for level in self.browse(cr, uid, rids, context):
            smallest_level_id = self.search(
                cr, uid,
                [('policy_id', '=', level.policy_id.id)],
                order='level asc', limit=1, context=context)
            smallest_level = self.browse(cr, uid, smallest_level_id[0], context)
            if smallest_level.computation_mode == 'previous_date':
                return False
        return True

    _sql_constraint = [('unique level',
                        'UNIQUE (policy_id, level)',
                        'Level must be unique per policy')]

    _constraints = [(_check_level_mode,
                     'The smallest level can not be of type Previous Reminder',
                     ['level'])]

    def _previous_level(self, cr, uid, policy_level, context=None):
        """ For one policy level, returns the id of the previous level

        If there is no previous level, it returns None, it means that's the
        first policy level

        :param browse_record policy_level: policy level
        :return: previous level id or None if there is no previous level
        """
        previous_level_ids = self.search(
            cr,
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

    def _get_sql_date_boundary_for_computation_mode(self, cr, uid, level, controlling_date, context=None):
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

    def _get_first_level_lines(self, cr, uid, level, controlling_date, lines, context=None):
        """Retrieve all the move lines that are linked to a first level.
           We use Raw SQL for performance. Security rule where applied in
           policy object when the first set of lines were retrieved"""
        level_lines = set()
        if not lines:
            return level_lines
        sql = ("SELECT DISTINCT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " WHERE mv_line.id in %(line_ids)s\n"
               " AND NOT EXISTS (SELECT cr_line.id from credit_control_line cr_line\n"
               "                  WHERE cr_line.move_line_id = mv_line.id)")
        sql += " AND" + self._get_sql_date_boundary_for_computation_mode(
                cr, uid, level, controlling_date, context)
        data_dict = {'controlling_date': controlling_date, 'line_ids': tuple(lines),
                     'delay': level.delay_days}

        cr.execute(sql, data_dict)
        res = cr.fetchall()
        if res:
            level_lines.update([x[0] for x in res])
        return level_lines

    def _get_other_level_lines(self, cr, uid, level, controlling_date, lines, context=None):
        """ Retrieve the move lines for other levels than first level.
        """
        level_lines = set()
        if not lines:
            return level_lines
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
                cr, uid, level, controlling_date, context)
        previous_level_id = self._previous_level(
                cr, uid, level, context=context)
        previous_level = self.browse(
                cr, uid, previous_level_id, context=context)
        data_dict =  {'controlling_date': controlling_date, 'line_ids': tuple(lines),
                     'delay': level.delay_days, 'level': previous_level.level}

        # print cr.mogrify(sql, data_dict)
        cr.execute(sql, data_dict)
        res = cr.fetchall()
        if res:
            level_lines.update([x[0] for x in res])
        return level_lines

    def get_level_lines(self, cr, uid, level_id, controlling_date, lines, context=None):
        """get all move lines in entry lines that match the current level"""
        assert not (isinstance(level_id, list) and len(level_id) > 1), \
            "level_id: only one id expected"
        if isinstance(level_id, list):
            level_id = level_id[0]
        matching_lines = set()
        level = self.browse(cr, uid, level_id, context=context)
        if self._previous_level(cr, uid, level, context=context) is None:
            method = self._get_first_level_lines
        else:
            method = self._get_other_level_lines

        matching_lines.update(
                method(cr, uid, level, controlling_date, lines, context=context))

        return matching_lines

