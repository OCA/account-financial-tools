# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Author: Leonardo Pistone
#   Copyright 2014 Camptocamp SA
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
"""Wizards for batch posting."""

import logging

from openerp import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.session import ConnectorSession
    from openerp.addons.connector.queue.job import job
except ImportError:
    _logger.debug('Can not `import connector`.')

    def empty_decorator(func):
        return func
    job = empty_decorator


class ValidateAccountMove(models.TransientModel):

    """Wizard to mark account moves for batch posting."""

    _inherit = "validate.account.move"

    action = fields.Selection([
        ('mark', 'Mark for posting'),
        ('unmark', 'Unmark for posting')],
        "Action",
        required=True,
        default='mark',
    )
    eta = fields.Integer('Seconds to wait before starting the jobs')
    asynchronous = fields.Boolean(
        'Use asynchronous validation',
        default=True,
    )

    @api.multi
    def validate_move(self):
        """Create a single job that will create one job per move.

        Return action.

        """
        self.ensure_one()
        session = ConnectorSession()
        # to find out what _classic_write does, read the documentation.
        wizard_data = self.read(self.id, load='_classic_write')
        if not wizard_data.get('asynchronous'):
            return super(ValidateAccountMove, self).validate_move()
        wizard_data.pop('id')
        if wizard_data.get('journal_ids'):
            journals_ids_vals = [(6, False,
                                  wizard_data.get('journal_ids'))]
            wizard_data['journal_ids'] = journals_ids_vals
        if wizard_data.get('period_ids'):
            periods_ids_vals = [(6, False,
                                wizard_data.get('period_ids'))]
            wizard_data['period_ids'] = periods_ids_vals

        if self.env.context.get('automated_test_execute_now'):
            process_wizard(session, self._name, wizard_data)
        else:
            process_wizard.delay(session, self._name, wizard_data)

        return {'type': 'ir.actions.act_window_close'}

    def process_wizard(self):
        """Choose the correct list of moves to mark and then validate."""
        for wiz in self:
            move_obj = self.env['account.move']
            domain = [('state', '=', 'draft'),
                      ('journal_id', 'in', wiz.journal_ids.ids),
                      ('period_id', 'in', wiz.period_ids.ids)]
            move_ids = move_obj.search(domain, order='date')
            if wiz.action == 'mark':
                move_ids.mark_for_posting(eta=wiz.eta)
            elif wiz.action == 'unmark':
                move_ids.unmark_for_posting()


@job
def process_wizard(session, model_name, wizard_data):
    """Create jobs to validate Journal Entries."""
    wiz_obj = session.env[model_name]
    new_wiz_id = wiz_obj.create(wizard_data)
    wiz_obj.process_wizard(ids=[new_wiz_id])
