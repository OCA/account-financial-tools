# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')


class AccountAsset(models.Model):

    _inherit = 'account.asset'

    @api.multi
    @job(default_channel='root.account_asset_batch_compute')
    def _compute_entries(self, date_end, check_triggers=False):
        if self.env.context.get(
            'asset_batch_processing', False
        ) and not self.env.context.get('test_queue_job_no_delay', False):
            results = []
            log_error = ''
            for record in self:
                description =\
                    _("Creating move for asset with id %s to %s") %\
                    (record.id, date_end)
                record.with_delay(
                    description=description)._compute_entries(
                    date_end, check_triggers=check_triggers)
            return results, log_error
        else:
            return super(AccountAsset, self)._compute_entries(
                date_end, check_triggers=check_triggers)
