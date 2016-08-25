# -*- coding: utf-8 -*-
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, _

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


class AccountAssetAsset(models.Model):

    _inherit = 'account.asset.asset'

    @api.multi
    def _compute_entries(self, period_id, check_triggers=False):
        if self.env.context.get('asset_batch_processing'):
            for record in self:
                session = ConnectorSession.from_env(self.env)
                description =\
                    _("Creating move for asset with id %s on period %s") %\
                    (record.id, period_id)
                async_compute_entries.delay(
                    session, record.id, period_id,
                    check_triggers=check_triggers, description=description)
            return []
        else:
            self.env.context = self.env.context.copy()
            return super(AccountAssetAsset, self)._compute_entries(
                period_id, check_triggers=check_triggers)


@job(default_channel='root.account_asset_batch_compute')
def async_compute_entries(session, asset_id, period_id,
                          check_triggers=False):
    asset = session.env['account.asset.asset'].browse([asset_id])[0]
    asset.with_context(asset_batch_processing=False)\
        ._compute_entries(period_id, check_triggers=check_triggers)
