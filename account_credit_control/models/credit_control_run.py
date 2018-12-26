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
    credit_control_count = fields.Integer(
        compute='_compute_credit_control_count',
        string='# of Credit Control Lines',
    )
    hide_change_state_button = fields.Boolean()
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'account.account'),
        index=True,
    )

    def _compute_credit_control_count(self):
        fetch_data = self.env['credit.control.line'].read_group(
            domain=[('run_id', 'in', self.ids)],
            fields=['run_id'],
            groupby=['run_id'],
        )
        result = {data['run_id'][0]: data['run_id_count']
                  for data in fetch_data}
        for rec in self:
            rec.credit_control_count = result.get(rec.id, 0)

    @api.model
    def _check_run_date(self, controlling_date):
        """ Ensure that there is no credit line in the future
        using controlling_date

        """
        runs = self.search(
            [('date', '>', controlling_date),
             ('company_id', '=', self.env.user.company_id.id)],
            order='date DESC',
            limit=1,
        )
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
                    "Credit Control Lines.<br/>") % policy.name

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

    def unlink(self):
        # Ondelete cascade don't check unlink lines restriction
        self.mapped('line_ids').unlink()
        return super().unlink()

    def open_credit_lines(self):
        """ Open the generated lines """
        self.ensure_one()
        action_name = 'account_credit_control.credit_control_line_action'
        action = self.env.ref(action_name)
        action = action.read()[0]
        action['domain'] = [('id', 'in', self.line_ids.ids)]
        return action

    def set_to_ready_lines(self):
        self.ensure_one()
        draft_lines = self.line_ids.filtered(lambda x: x.state == 'draft')
        draft_lines.write({'state': 'to_be_sent'})
        self.hide_change_state_button = True
        # if not draft_lines:
        #     raise UserError(_('No lines in draft state'))
        # action_name = ('account_credit_control'
        #                '.open_credit_line_marker_wizard_menu_action')
        # action = self.env.ref(action_name)
        # action = action.read()[0]
        # action['context'] = {
        #     'active_model': 'credit.control.line',
        #     'active_ids': draft_lines.ids,
        # }
        # return action

    def run_channel_action(self):
        self.ensure_one()
        lines = self.line_ids.filtered(lambda x: x.state == 'to_be_sent')
        letter_lines = lines.filtered(lambda x: x.channel == 'letter')
        email_lines = lines.filtered(lambda x: x.channel == 'email')
        if email_lines:
            comm_obj = self.env['credit.control.communication']
            comms = comm_obj._generate_comm_from_credit_lines(email_lines)
            comms._generate_emails()
        if letter_lines:
            wiz = self.env['credit.control.printer'].create({
                'line_ids': letter_lines.ids,
            })
            return wiz.print_lines
