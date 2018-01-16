# -*- coding: utf-8 -*-
# Copyright 2014 Leonardo Pistone Camptocamp SA
# Copyright 2018 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from openerp import models, fields, api

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

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journal',
    )
    date_start = fields.Date(required=True)
    date_end = fields.Date(required=True)
    action = fields.Selection(
        [('mark', 'Mark for posting'),
         ('unmark', 'Unmark for posting')],
        "Action", required=True, default='mark',
    )
    eta = fields.Integer(
        'Seconds to wait before starting the jobs'
    )
    asynchronous = fields.Boolean(
        'Use asynchronous validation',
        default=True,
    )

    def _search_move(self):
        move_obj = self.env['account.move']

        domain = [('state', '=', 'draft'),
                  ('date', '>=', self.date_start),
                  ('date', '<=', self.date_end)]

        if self.journal_ids:
            domain.append(
                ('journal_id', 'in', self.journal_ids.ids)
            )

        move_ids = move_obj.search(domain, order='date')

        return move_ids

    @api.multi
    def validate_move(self):
        """Create a single job that will create one job per move.
        Return action.
        """
        session = ConnectorSession.from_env(self.env)
        # to find out what _classic_write does, read the documentation.

        if not self.asynchronous:
            move_ids = self._search_move()

            return super(ValidateAccountMove,
                         self.with_context(active_ids=move_ids.ids)
                         ).validate_move()

        wizard_data = {
            'journal_ids': self.journal_ids.ids,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'action': self.action,
            'eta': self.eta,
        }

        if self.env.context.get('automated_test_execute_now'):
            process_wizard(session, self._name, wizard_data)
        else:
            process_wizard.delay(session, self._name, wizard_data)

        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def process_wizard(self):
        """Choose the correct list of moves to mark and then validate."""
        for wiz in self:
            move_ids = self._search_move()

            if wiz.action == 'mark':
                move_ids.mark_for_posting(eta=wiz.eta)

            elif wiz.action == 'unmark':
                move_ids.unmark_for_posting()


@job
def process_wizard(session, model_name, wizard_data):
    """Create jobs to validate Journal Entries."""

    wiz_obj = session.env[model_name]
    new_wiz_id = wiz_obj.create(
        wizard_data,
    )
    if wizard_data.get('journal_ids'):
        new_wiz_id.journal_ids = [(6, 0, wizard_data.get('journal_ids'))]

    new_wiz_id.process_wizard()
