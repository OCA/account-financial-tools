# -*- coding: utf-8 -*-
# Author: Lam Thai Binh
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import datetime
import logging

from odoo import fields
from odoo.tests.common import TransactionCase


class TestCurrencyRateUpdate(TransactionCase):

    def setUp(self):
        super(TestCurrencyRateUpdate, self).setUp()
        self.env.user.company_id.auto_currency_up = True
        self.env.cr.execute(
            """UPDATE res_company SET currency_id = %s
            WHERE id = %s""",
            (self.env.user.company_id.id, self.env.ref('base.EUR').id),
        )
        self.service_env = self.env['currency.rate.update.service']
        self.rate_env = self.env['res.currency.rate']

    def _test_cron_by_service(self, service_code, currency_xml_ids):
        """Test the ir.cron with any service for some currencies
        """
        currency_ids = [
            self.env.ref(currency_xml_id).id
            for currency_xml_id in currency_xml_ids]

        service_x = self.service_env.create({
            'service': service_code,
            'currency_to_update': [(6, 0, currency_ids)]
        })

        rate_name = \
            fields.Datetime.to_string(datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0))
        for currency_id in currency_ids:
            rates = self.rate_env.search([
                ('currency_id', '=', currency_id),
                ('company_id', '=', self.env.user.company_id.id),
                ('name', '=', rate_name)])
            rates.unlink()
        self.service_env._run_currency_update()
        logging.info("Service note: %s", service_x.note)
        self.assertFalse('ERROR' in service_x.note)

    # FIXME: except_orm(u'Error !', u'Exchange data for USD is not reported
    # by Bank of Canada.')
    # def test_cron_CA_BOC(self):
    #     """Test the ir.cron with Bank of Canada service for USD
    #     """
    #     self._test_cron_by_service('CA_BOC', ['base.USD'])

    def test_cron_CH_ADMIN(self):
        """Test the ir.cron with Admin.ch service for USD
        """
        self._test_cron_by_service('CH_ADMIN', ['base.USD'])

    def test_cron_ECB(self):
        """Test the ir.cron with European Central Bank service for USD
        """
        self._test_cron_by_service('ECB', ['base.USD'])

    def test_cron_MX_BdM(self):
        """Test the ir.cron with Bank of Mexico service for USD
        """
        self._test_cron_by_service('MX_BdM', ['base.USD'])

    def test_cron_PL_NBP(self):
        """Test the ir.cron with National Bank of Poland service for USD
        """
        self._test_cron_by_service('PL_NBP', ['base.USD'])

    def test_cron_RO_BNR(self):
        """Test the ir.cron with National Bank of Romania service for USD
        """
        self._test_cron_by_service('RO_BNR', ['base.USD'])

    def test_cron_VN_VCB(self):
        """Test the ir.cron with Vietcombank service for USD
        """
        self._test_cron_by_service('VN_VCB', ['base.USD'])
