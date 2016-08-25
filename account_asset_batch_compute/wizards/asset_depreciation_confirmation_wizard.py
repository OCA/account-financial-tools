# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.session import ConnectorSession
    from openerp.addons.connector.queue.job import job
except ImportError:
    _logger.debug('Can not `import connector`.')

    def empty_decorator(func):
        return func
    job = empty_decorator


class AssetDepreciationConfirmationWizard(models.TransientModel):

    _inherit = 'asset.depreciation.confirmation.wizard'

    batch_processing = fields.Boolean()

    @api.multi
    def asset_compute(self):
        self.ensure_one()
        if not self.batch_processing:
            return super(AssetDepreciationConfirmationWizard, self)\
                .asset_compute()
        if self.env.context.get('not_async'):
            return super(AssetDepreciationConfirmationWizard,
                         self.with_context(asset_batch_processing=True))\
                         .asset_compute()
        else:
            session = ConnectorSession.from_env(self.env)
            description =\
                _("Creating jobs to create moves for assets period %s") % (
                    self.period_id.id,)
            async_asset_compute.delay(session, self.period_id.id,
                                      description=description)


@job(default_channel='root.account_asset_batch_compute')
def async_asset_compute(session, period_id):
    model = session.env['asset.depreciation.confirmation.wizard']
    obj = model.create({'period_id': period_id,
                        'batch_processing': True})
    obj.with_context(not_async=True).asset_compute()
