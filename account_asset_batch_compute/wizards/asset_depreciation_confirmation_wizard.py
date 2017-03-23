# -*- coding: utf-8 -*-
# Copyright 2016-2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug('Can not `import queue_job`.')

    def empty_decorator(func):
        return func
    job = empty_decorator


class AssetDepreciationConfirmationWizard(models.TransientModel):

    _inherit = 'asset.depreciation.confirmation.wizard'

    batch_processing = fields.Boolean()

    @api.multi
    @job(default_channel='root.account_asset_batch_compute')
    def asset_compute(self):
        self.ensure_one()
        if not self.batch_processing:
            return super(AssetDepreciationConfirmationWizard, self)\
                .asset_compute()
        if not self.env.context.get('job_uuid'):
            description = \
                _("Creating jobs to create moves for assets to %s") % (
                    self.date_end,)
            job = self.with_delay(description=description).asset_compute()
            return u'Job created with uuid %s' % (job.uuid,)
        else:
            self = self.with_context(asset_batch_processing=True)
            return super(AssetDepreciationConfirmationWizard, self)\
                .asset_compute()
