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

logger = logging.getLogger('credit.control.run')


class CreditControlRun(orm.Model):
    """Credit Control run generate all credit control lines and reject"""

    _name = "credit.control.run"
    _rec_name = 'date'
    _description = """Credit control line generator"""
    _columns = {
        'date': fields.date('Controlling Date', required=True),
        'policy_ids':
            fields.many2many('credit.control.policy',
                             rel="credit_run_policy_rel",
                             id1='run_id', id2='policy_id',
                             string='Policies',
                             readonly=True,
                             states={'draft': [('readonly', False)]}),

        'report': fields.text('Report', readonly=True),

        'state': fields.selection([('draft', 'Draft'),
                                   ('done', 'Done')],
                                  string='State',
                                  required=True,
                                  readonly=True),

        'manual_ids':
            fields.many2many('account.move.line',
                             rel="credit_runreject_rel",
                             string='Lines to handle manually',
                             help=('If a credit control line has been generated'
                                   'on a policy and the policy has been changed '
                                   'in the meantime, it has to be handled '
                                   'manually'),
                             readonly=True),
        }

    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.update({
            'report': False,
            'manual_ids': False,
        })
        return super(CreditControlRun, self).copy_data(
            cr, uid, id, default=default, context=context)

    def _get_policies(self, cr, uid, context=None):
        return self.pool['credit.control.policy'].search(cr, uid, [], context=context)

    _defaults = {'state': 'draft',
                 'policy_ids': _get_policies}

    def _check_run_date(self, cr, uid, ids, controlling_date, context=None):
        """Ensure that there is no credit line in the future using controlling_date"""
        run_obj = self.pool['credit.control.run']
        runs = run_obj.search(cr, uid, [('date', '>', controlling_date)],
                              order='date DESC', limit=1, context=context)
        if runs:
            run = run_obj.browse(cr, uid, runs[0], context=context)
            raise orm.except_orm(_('Error'),
                                 _('A run has already been executed more '
                                   'recently than %s') % (run.date))

        line_obj = self.pool['credit.control.line']
        lines = line_obj.search(cr, uid, [('date', '>', controlling_date)],
                                order='date DESC', limit=1, context=context)
        if lines:
            line = line_obj.browse(cr, uid, lines[0], context=context)
            raise orm.except_orm(_('Error'),
                                 _('A credit control line more '
                                   'recent than %s exists at %s') %
                                 (controlling_date, line.date))
        return True

    def _generate_credit_lines(self, cr, uid, run_id, context=None):
        """ Generate credit control lines. """
        cr_line_obj = self.pool.get('credit.control.line')
        assert not (isinstance(run_id, list) and len(run_id) > 1), \
            "run_id: only one id expected"
        if isinstance(run_id, list):
            run_id = run_id[0]

        run = self.browse(cr, uid, run_id, context=context)
        manually_managed_lines = set()  # line who changed policy
        credit_line_ids = []  # generated lines
        run._check_run_date(run.date, context=context)

        policies = run.policy_ids
        if not policies:
            raise orm.except_orm(_('Error'),
                                 _('Please select a policy'))

        report = ''
        generated_ids = []
        for policy in policies:
            if policy.do_nothing:
                continue
            lines = policy._get_move_lines_to_process(run.date, context=context)
            manual_lines = policy._lines_different_policy(lines, context=context)
            lines.difference_update(manual_lines)
            manually_managed_lines.update(manual_lines)
            policy_generated_ids = []
            if lines:
                # policy levels are sorted by level so iteration is in the correct order
                for level in reversed(policy.level_ids):
                    level_lines = level.get_level_lines(run.date, lines, context=context)
                    policy_generated_ids += cr_line_obj.create_or_update_from_mv_lines(
                        cr, uid, [], list(level_lines), level.id, run.date, context=context)
            generated_ids.extend(policy_generated_ids)
            if policy_generated_ids:
                report += _("Policy \"%s\" has generated %d Credit Control Lines.\n") % \
                        (policy.name, len(policy_generated_ids))
                credit_line_ids += policy_generated_ids
            else:
                report += _("Policy \"%s\" has not generated any Credit Control Lines.\n" %
                        policy.name)

        vals = {'state': 'done',
                'report': report,
                'manual_ids': [(6, 0, manually_managed_lines)]}
        run.write(vals, context=context)
        return generated_ids

    def generate_credit_lines(self, cr, uid, run_id, context=None):
        """Generate credit control lines

        Lock the ``credit_control_run`` Postgres table to avoid concurrent
        calls of this method.
        """
        try:
            cr.execute('SELECT id FROM credit_control_run'
                       ' LIMIT 1 FOR UPDATE NOWAIT')
        except Exception as exc:
            # in case of exception openerp will do a rollback for us and free the lock
            raise orm.except_orm(_('Error'),
                                 _('A credit control run is already running'
                                   ' in background, please try later.'))

        self._generate_credit_lines(cr, uid, run_id, context)
        return True
