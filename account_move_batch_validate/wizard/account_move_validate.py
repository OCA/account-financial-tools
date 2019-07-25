# Copyright 2014 Camptocamp SA, 2017 ACSONE
# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


class AccountMoveValidate(models.TransientModel):

    _inherit = 'validate.account.move'

    action = fields.Selection(
        selection='_get_actions', string="Action",
        required=True, default='mark')
    eta = fields.Integer(string="Seconds to wait before starting the jobs")
    asynchronous = fields.Boolean(string="Use asynchronous validation")

    @api.model
    def _get_actions(self):
        return [
            ('mark', _('Mark for posting')),
            ('unmark', _('Unmark for posting'))
        ]

    @api.multi
    def validate_move(self):
        self.ensure_one()

        if not self.asynchronous:
            return super().validate_move()

        wizard_data = {
            'move_ids': self.env.context.get('active_ids'),
            'action': self.action,
            'asynchronous': self.asynchronous,
            'eta': self.eta,
        }

        if self.env.context.get('automated_test_execute_now'):
            return self.process_wizard(wizard_data)
        else:
            return self.env[self._name].with_delay(priority=5).process_wizard(
                wizard_data)

    @job()
    def process_wizard(self, wizard_data):
        AccountMoveObj = self.env['account.move']

        move_ids = wizard_data.get('move_ids')
        action = wizard_data.get('action')
        eta = wizard_data.get('eta')

        moves = AccountMoveObj.search([
            ('id', 'in', move_ids),
            ('state', '=', 'draft')
        ])

        if action == 'mark':
            moves.mark_for_posting(eta=eta)
        elif action == 'unmark':
            moves.unmark_for_posting()
