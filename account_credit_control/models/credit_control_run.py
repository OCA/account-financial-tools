# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class CreditControlRun(models.Model):
    """ Credit Control run generate all credit control lines and reject """

    _name = "credit.control.run"
    _rec_name = 'date'
    _description = "Credit control line generator"

    @api.model
    def _default_policies(self):
        return self.env['credit.control.policy'].search([])

    date = fields.Date(string='Controlling Date', required=True,
                       readonly=True,
                       states={'draft': [('readonly', False)]})
    policy_ids = fields.Many2many(
        'credit.control.policy',
        relation="credit_run_policy_rel",
        column1='run_id', column2='policy_id',
        string='Policies',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self._default_policies(),
    )
    report = fields.Html(readonly=True, copy=False)
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')],
                             required=True,
                             readonly=True,
                             default='draft')
    line_ids = fields.One2many(
        comodel_name='credit.control.line',
        inverse_name='run_id',
        string='Generated lines')
    manual_ids = fields.Many2many(
        'account.move.line',
        rel="credit_runreject_rel",
        string='Lines to handle manually',
        help='If a credit control line has been generated'
             'on a policy and the policy has been changed '
             'in the meantime, it has to be handled '
             'manually',
        readonly=True,
        copy=False,
    )

    @api.model
    def _check_run_date(self, controlling_date):
        """ Ensure that there is no credit line in the future
        using controlling_date

        """
        runs = self.search([('date', '>', controlling_date)],
                           order='date DESC', limit=1)
        if runs:
            raise UserError(_('A run has already been executed more '
                              'recently than %s') % (runs.date))

        line_obj = self.env['credit.control.line']
        lines = line_obj.search([('date', '>', controlling_date)],
                                order='date DESC', limit=1)
        if lines:
            raise UserError(_('A credit control line more '
                              'recent than %s exists at %s') %
                            (controlling_date, lines.date))

    @api.multi
    @api.returns('credit.control.line')
    def _generate_credit_lines(self):
        """ Generate credit control lines. """
        self.ensure_one()
        manually_managed_lines = self.env['account.move.line']
        self._check_run_date(self.date)

        policies = self.policy_ids
        if not policies:
            raise UserError(_('Please select a policy'))

        report = ''
        generated = self.env['credit.control.line']
        for policy in policies:
            if policy.do_nothing:
                continue
            lines = policy._get_move_lines_to_process(self.date)
            manual_lines = policy._lines_different_policy(lines)
            lines -= manual_lines
            manually_managed_lines |= manual_lines
            policy_lines_generated = self.env['credit.control.line']
            if lines:
                # policy levels are sorted by level
                # so iteration is in the correct order
                create = policy_lines_generated.create_or_update_from_mv_lines
                for level in reversed(policy.level_ids):
                    level_lines = level.get_level_lines(self.date, lines)
                    policy_lines_generated += create(level_lines,
                                                     level,
                                                     self.date)
            generated |= policy_lines_generated
            if policy_lines_generated:
                report += (_("Policy \"<b>%s</b>\" has generated <b>%d Credit "
                             "Control Lines.</b><br/>") %
                            (policy.name, len(policy_lines_generated)))
            else:
                report += _(
                    "Policy \"<b>%s</b>\" has not generated any "
                    "Credit Control Lines.<br/>" % policy.name
                )

        vals = {'state': 'done',
                'report': report,
                'manual_ids': [(6, 0, manually_managed_lines.ids)],
                'line_ids': [(6, 0, generated.ids)]}
        self.write(vals)
        return generated

    @api.multi
    def generate_credit_lines(self):
        """ Generate credit control lines

        Lock the ``credit_control_run`` Postgres table to avoid concurrent
        calls of this method.
        """
        try:
            self.env.cr.execute('SELECT id FROM credit_control_run'
                                ' LIMIT 1 FOR UPDATE NOWAIT')
        except Exception:
            # In case of exception openerp will do a rollback
            # for us and free the lock
            raise UserError(_('A credit control run is already running '
                              'in background, please try later.'))

        self._generate_credit_lines()
        return True

    @api.multi
    def open_credit_lines(self):
        """ Open the generated lines """
        self.ensure_one()
        action_name = 'account_credit_control.credit_control_line_action'
        action = self.env.ref(action_name)
        action = action.read()[0]
        action['domain'] = [('id', 'in', self.line_ids.ids)]
        return action
