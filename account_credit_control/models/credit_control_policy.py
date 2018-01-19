# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CreditControlPolicy(models.Model):
    """ Define a policy of reminder """

    _name = "credit.control.policy"
    _description = """Define a reminder policy"""

    name = fields.Char(required=True)
    level_ids = fields.One2many('credit.control.policy.level',
                                'policy_id',
                                string='Policy Levels')
    do_nothing = fields.Boolean(help='For policies which should not '
                                     'generate lines or are obsolete')
    company_id = fields.Many2one('res.company', string='Company')
    account_ids = fields.Many2many(
        'account.account',
        string='Accounts',
        required=True,
        domain="[('internal_type', '=', 'receivable')]",
        help="This policy will be active only"
             " for the selected accounts",
    )
    active = fields.Boolean(default=True)

    @api.multi
    def _move_lines_domain(self, controlling_date):
        """ Build the default domain for searching move lines """
        self.ensure_one()
        return [('account_id', 'in', self.account_ids.ids),
                ('date_maturity', '<=', controlling_date),
                ('reconciled', '=', False),
                ('partner_id', '!=', False)]

    @api.multi
    @api.returns('account.move.line')
    def _due_move_lines(self, controlling_date):
        """ Get the due move lines for the policy of the company.

        The set of ids will be reduced and extended according
        to the specific policies defined on partners and invoices.

        Do not use direct SQL in order to respect security rules.

        Assume that only the receivable lines have a maturity date and that
        accounts used in the policy are reconcilable.
        """
        self.ensure_one()
        move_l_obj = self.env['account.move.line']
        user = self.env.user
        if user.company_id.credit_policy_id.id != self.id:
            return move_l_obj
        domain_line = self._move_lines_domain(controlling_date)
        return move_l_obj.search(domain_line)

    @api.multi
    @api.returns('account.move.line')
    def _move_lines_subset(self, controlling_date, model, move_relation_field):
        """ Get the move lines related to one model for a policy.

        Do not use direct SQL in order to respect security rules.

        Assume that only the receivable lines have a maturity date and that
        accounts used in the policy are reconcilable.

        The policy relation field must be named credit_policy_id.

        :param str controlling_date: date of credit control
        :param str model: name of the model where is defined a credit_policy_id
        :param str move_relation_field: name of the field in account.move.line
            which is a many2one to `model`
        :return: recordset to add in the process, recordset to remove from
            the process
        """
        self.ensure_one()
        # MARK possible place for a good optimisation
        my_obj = self.env[model]
        default_domain = self._move_lines_domain(controlling_date)

        to_add = self.env['account.move.line']
        to_remove = self.env['account.move.line']

        # The lines which are linked to this policy have to be included in the
        # run for this policy.
        # If another object override the credit_policy_id (ie. invoice after
        add_objs = my_obj.search([('credit_policy_id', '=', self.id)])
        if add_objs:
            domain = list(default_domain)
            domain.append((move_relation_field, 'in', add_objs.ids))
            to_add = to_add.search(domain)

        # The lines which are linked to another policy do not have to be
        # included in the run for this policy.
        neg_objs = my_obj.search([('credit_policy_id', '!=', self.id),
                                  ('credit_policy_id', '!=', False)])
        if neg_objs:
            domain = list(default_domain)
            domain.append((move_relation_field, 'in', neg_objs.ids))
            to_remove = to_remove.search(domain)
        return to_add, to_remove

    @api.multi
    @api.returns('account.move.line')
    def _get_partner_related_lines(self, controlling_date):
        """ Get the move lines for a policy related to a partner.

        :param str controlling_date: date of credit control
        :param str model: name of the model where is defined a credit_policy_id
        :param str move_relation_field: name of the field in account.move.line
            which is a many2one to `model`
        :return: recordset to add in the process, recordset to remove from
            the process
        """
        return self._move_lines_subset(controlling_date, 'res.partner',
                                       'partner_id')

    @api.multi
    @api.returns('account.move.line')
    def _get_invoice_related_lines(self, controlling_date):
        """ Get the move lines for a policy related to an invoice.

        :param str controlling_date: date of credit control
        :param str model: name of the model where is defined a credit_policy_id
        :param str move_relation_field: name of the field in account.move.line
            which is a many2one to `model`
        :return: recordset to add in the process, recordset to remove from
            the process
        """
        return self._move_lines_subset(controlling_date, 'account.invoice',
                                       'invoice_id')

    @api.multi
    @api.returns('account.move.line')
    def _get_move_lines_to_process(self, controlling_date):
        """ Build a list of move lines ids to include in a run
        for a policy at a given date.

        :param str controlling_date: date of credit control
        :return: recordset to include in the run
        """
        self.ensure_one()
        # there is a priority between the lines, depicted by the calls below
        lines = self._due_move_lines(controlling_date)
        to_add, to_remove = self._get_partner_related_lines(controlling_date)
        lines = (lines | to_add) - to_remove
        to_add, to_remove = self._get_invoice_related_lines(controlling_date)
        lines = (lines | to_add) - to_remove
        return lines

    @api.multi
    @api.returns('account.move.line')
    def _lines_different_policy(self, lines):
        """ Return a set of move lines ids for which there is an
            existing credit line but with a different policy.
        """
        self.ensure_one()
        different_lines = self.env['account.move.line']
        if not lines:
            return different_lines
        cr = self.env.cr
        cr.execute("SELECT move_line_id FROM credit_control_line"
                   "    WHERE policy_id != %s and move_line_id in %s"
                   "    AND manually_overridden IS false",
                   (self.id, tuple(lines.ids)))
        res = cr.fetchall()
        if res:
            return different_lines.browse([row[0] for row in res])
        return different_lines

    @api.multi
    def check_policy_against_account(self, account):
        """ Ensure that the policy corresponds to account relation """
        allowed = self.search(['|', ('account_ids', 'in', account.ids),
                               ('do_nothing', '=', True)])
        if self not in allowed:
            allowed_names = "\n".join(x.name for x in allowed)
            raise UserError(
                _('You can only use a policy set on '
                  'account %s.\n'
                  'Please choose one of the following '
                  'policies:\n %s') % (account.name, allowed_names)
            )
        return True


class CreditControlPolicyLevel(models.Model):
    """Define a policy level. A level allows to determine if
    a move line is due and the level of overdue of the line"""

    _name = "credit.control.policy.level"
    _order = 'level'
    _description = """A credit control policy level"""

    name = fields.Char(required=True, translate=True)
    policy_id = fields.Many2one('credit.control.policy',
                                string='Related Policy',
                                required=True)
    level = fields.Integer(required=True)
    computation_mode = fields.Selection(
        [('net_days', 'Due Date'),
         ('end_of_month', 'Due Date, End Of Month'),
         ('previous_date', 'Previous Reminder')],
        string='Compute Mode',
        required=True
    )
    delay_days = fields.Integer(string='Delay (in days)', required=True)
    email_template_id = fields.Many2one('mail.template',
                                        string='Email Template',
                                        required=True)
    channel = fields.Selection([('letter', 'Letter'),
                                ('email', 'Email')],
                               required=True)
    custom_text = fields.Text(string='Custom Message',
                              required=True,
                              translate=True)
    custom_mail_text = fields.Html(string='Custom Mail Message',
                                   required=True, translate=True)
    custom_text_after_details = fields.Text(
        string='Custom Message after details', translate=True)

    _sql_constraint = [('unique level',
                        'UNIQUE (policy_id, level)',
                        'Level must be unique per policy')]

    @api.multi
    @api.constrains('level', 'computation_mode')
    def _check_level_mode(self):
        """ The smallest level of a policy cannot be computed on the
        "previous_date".
        """

        for policy_level in self:
            smallest_level = \
                self.search([('policy_id', '=', policy_level.policy_id.id)],
                            order='level asc', limit=1)
            if smallest_level.computation_mode == 'previous_date':
                raise ValidationError(_('The smallest level can not be '
                                        'of type Previous Reminder'))

    @api.multi
    def _previous_level(self):
        """ For one policy level, returns the id of the previous level

        If there is no previous level, it returns None, it means that's the
        first policy level

        :return: previous level or None if there is no previous level
        """
        self.ensure_one()
        previous_levels = self.search([('policy_id', '=', self.policy_id.id),
                                       ('level', '<', self.level)],
                                      order='level desc',
                                      limit=1)
        if not previous_levels:
            return None
        return previous_levels

    # ----- sql time related methods ---------

    @staticmethod
    def _net_days_get_boundary():
        return (" (mv_line.date_maturity + %(delay)s)::date <= "
                "date(%(controlling_date)s)")

    @staticmethod
    def _end_of_month_get_boundary():
        return ("(date_trunc('MONTH', (mv_line.date_maturity + %(delay)s))+"
                "INTERVAL '1 MONTH - 1 day')::date"
                "<= date(%(controlling_date)s)")

    @staticmethod
    def _previous_date_get_boundary():
        return "(cr_line.date + %(delay)s)::date <= date(%(controlling_date)s)"

    @api.multi
    def _get_sql_date_boundary_for_computation_mode(self):
        """ Return a where clauses statement for the given controlling
        date and computation mode of the level
        """
        self.ensure_one()
        fname = "_%s_get_boundary" % (self.computation_mode, )
        if hasattr(self, fname):
            fnc = getattr(self, fname)
            return fnc()
        else:
            raise NotImplementedError(
                _('Can not get function for computation mode: '
                  '%s is not implemented') % (fname, )
            )

    # -----------------------------------------

    @api.multi
    @api.returns('account.move.line')
    def _get_first_level_move_lines(self, controlling_date, lines):
        """ Retrieve all the move lines that are linked to a first level.
        We use Raw SQL for performance. Security rule where applied in
        policy object when the first set of lines were retrieved
        """
        self.ensure_one()
        move_line_obj = self.env['account.move.line']
        if not lines:
            return move_line_obj
        cr = self.env.cr
        sql = ("SELECT DISTINCT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " WHERE mv_line.id in %(line_ids)s\n"
               " AND NOT EXISTS (SELECT id\n"
               "                 FROM credit_control_line\n"
               "                 WHERE move_line_id = mv_line.id\n"
               # lines from a previous level with a draft or ignored state
               # or manually overridden
               # have to be generated again for the previous level
               "                 AND NOT manually_overridden\n"
               "                 AND state NOT IN ('draft', 'ignored'))"
               " AND (mv_line.debit IS NOT NULL AND mv_line.debit != 0.0)\n")
        sql += " AND"
        _get_sql_date_part = self._get_sql_date_boundary_for_computation_mode
        sql += _get_sql_date_part()
        data_dict = {'controlling_date': controlling_date,
                     'line_ids': tuple(lines.ids),
                     'delay': self.delay_days}
        cr.execute(sql, data_dict)
        res = cr.fetchall()
        if res:
            return move_line_obj.browse([row[0] for row in res])
        return move_line_obj

    @api.multi
    @api.returns('account.move.line')
    def _get_other_level_move_lines(self, controlling_date, lines):
        """ Retrieve the move lines for other levels than first level.
        """
        self.ensure_one()
        move_line_obj = self.env['account.move.line']
        if not lines:
            return move_line_obj
        cr = self.env.cr
        sql = ("SELECT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " JOIN credit_control_line cr_line\n"
               " ON (mv_line.id = cr_line.move_line_id)\n"
               " WHERE cr_line.id = (SELECT credit_control_line.id "
               " FROM credit_control_line\n"
               "      WHERE credit_control_line.move_line_id = mv_line.id\n"
               "      AND state != 'ignored'"
               "      AND NOT manually_overridden"
               "      ORDER BY credit_control_line.level desc limit 1)\n"
               " AND cr_line.level = %(previous_level)s\n"
               " AND (mv_line.debit IS NOT NULL AND mv_line.debit != 0.0)\n"
               # lines from a previous level with a draft or ignored state
               # or manually overridden
               # have to be generated again for the previous level
               " AND NOT manually_overridden\n"
               " AND cr_line.state NOT IN ('draft', 'ignored')\n"
               " AND mv_line.id in %(line_ids)s\n")
        sql += " AND "
        _get_sql_date_part = self._get_sql_date_boundary_for_computation_mode
        sql += _get_sql_date_part()
        previous_level = self._previous_level()
        data_dict = {'controlling_date': controlling_date,
                     'line_ids': tuple(lines.ids),
                     'delay': self.delay_days,
                     'previous_level': previous_level.level}

        # print cr.mogrify(sql, data_dict)
        cr.execute(sql, data_dict)
        res = cr.fetchall()
        if res:
            return move_line_obj.browse([row[0] for row in res])
        return move_line_obj

    @api.multi
    @api.returns('account.move.line')
    def get_level_lines(self, controlling_date, lines):
        """ get all move lines in entry lines that match the current level """
        self.ensure_one()
        matching_lines = self.env['account.move.line']
        if self._previous_level() is None:
            method = self._get_first_level_move_lines
        else:
            method = self._get_other_level_move_lines
        matching_lines |= method(controlling_date, lines)
        return matching_lines
