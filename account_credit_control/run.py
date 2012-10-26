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
import sys
import traceback
import logging

from openerp.osv.orm import Model, fields
from openerp.tools.translate import _
from openerp.osv.osv import except_osv

logger = logging.getLogger('Credit Control run')

# beware, do always use the DB lock of `CreditControlRun.generate_credit_lines`
# to use this variable, otherwise you will have race conditions
memoizers = {}


class CreditControlRun(Model):
    """Credit Control run generate all credit control lines and reject"""

    _name = "credit.control.run"
    _rec_name = 'date'
    _description = """Credit control line generator"""
    _columns = {
        'date': fields.date('Controlling Date', required=True),
        'policy_ids': fields.many2many('credit.control.policy',
                                        rel="credit_run_policy_rel",
                                        id1='run_id', id2='policy_id',
                                        string='Policies',
                                        readonly=True,
                                        states={'draft': [('readonly', False)]}),

        'report': fields.text('Report', readonly=True),

        'state': fields.selection([('draft', 'Draft'),
                                   ('running', 'Running'),
                                   ('done', 'Done'),
                                   ('error', 'Error')],
                                   string='State',
                                   required=True,
                                   readonly=True),

        'manual_ids': fields.many2many('account.move.line',
                                        rel="credit_runreject_rel",
                                        string='Lines to handle manually',
                                        readonly=True),
    }

    def _get_policies(self, cursor, uid, context=None):
        return self.pool.get('credit.control.policy').\
                search(cursor, uid, [], context=context)

    _defaults = {
        'state': 'draft',
        'policy_ids': _get_policies,
    }

    def _check_run_date(self, cursor, uid, ids, controlling_date, context=None):
        """Ensure that there is no credit line in the future using controlling_date"""
        line_obj =  self.pool.get('credit.control.line')
        lines = line_obj.search(cursor, uid, [('date', '>', controlling_date)],
                                order='date DESC', limit=1, context=context)
        if lines:
            line = line_obj.browse(cursor, uid, lines[0], context=context)
            raise except_osv(_('A run has already been executed more recently than %s') % (line.date))
        return True

    def _generate_credit_lines(self, cursor, uid, run_id, context=None):
        """ Generate credit control lines. """
        memoizers['credit_line_residuals'] = {}
        cr_line_obj = self.pool.get('credit.control.line')
        assert not (isinstance(run_id, list) and len(run_id) > 1), \
                "run_id: only one id expected"
        if isinstance(run_id, list):
            run_id = run_id[0]

        run = self.browse(cursor, uid, run_id, context=context)
        errors = []
        manually_managed_lines = []  # line who changed policy
        credit_line_ids = []  # generated lines
        run._check_run_date(run.date, context=context)

        policy_ids = run.policy_ids
        if not policy_ids:
            raise except_osv(
                _('Error'),
                _('Please select a policy'))

        lines = []
        for policy in policy_ids:
            if policy.do_nothing:
                continue
            try:
                lines = policy._get_moves_line_to_process(run.date, context=context)
                tmp_manual = policy._check_lines_policies(lines, context=context)
                # FIXME why do not use only sets instead of converting them each
                # time ?
                lines = list(set(lines) - set(tmp_manual))
                manually_managed_lines += tmp_manual
                if not lines:
                    continue
                # policy levels are sorted by level so iteration is in the correct order
                for level in policy.level_ids:
                    level_lines = level.get_level_lines(run.date, lines, context=context)
                    # only this write action own a separate cursor
                    loc_ids, loc_errors = cr_line_obj.create_or_update_from_mv_lines(
                        cursor, uid, [], level_lines, level.id, run.date, context=context)
                    credit_line_ids += loc_ids
                    errors += loc_errors

                lines = list(set(lines) - set(level_lines))
            except except_osv, exc:
                # TODO: check if rollback on cursor is safe ?
                cursor.rollback()
                error_type, error_value, trbk = sys.exc_info()
                st = "Error: %s\nDescription: %s\nTraceback:" % (error_type.__name__, error_value)
                st += ''.join(traceback.format_tb(trbk, 30))
                logger.error(st)
                self.write(cursor, uid,
                           [run.id],
                           {'report':st,
                            'state': 'error'},
                           context=context)
                return False
            vals = {'report': u"Number of generated lines : %s \n" % (len(credit_line_ids),),
                    'manual_ids': [(6, 0, manually_managed_lines)]}

            if errors:
                vals['report'] += u"Following line generation errors appends:"
                vals['report'] += u"----\n".join(errors)

            run.write(vals, context=context)
        run.write({'state': 'done'}, context=context)
        # lines will correspond to line that where not treated
        return lines

    def generate_credit_lines(self, cursor, uid, run_id, context=None):
        """Generate credit control lines

        Lock the ``credit_control_run`` Postgres table to avoid concurrent
        calls of this method.
        """
        if context is None:
            context = {}
        try:
            cursor.execute('SELECT id FROM credit_control_run'
                           ' LIMIT 1 FOR UPDATE NOWAIT' )
        except Exception, exc:
            cursor.rollback()
            raise except_osv(_('A credit control run is already running'
                               ' in background please try later'),
                             str(exc))
        # in case of exception openerp will do a rollback for us and free the lock
        return self._generate_credit_lines(cursor, uid, run_id, context)

