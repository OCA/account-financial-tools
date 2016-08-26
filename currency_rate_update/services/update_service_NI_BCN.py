# -*- coding: utf-8 -*-
# © 2009 Camptocamp
# © 2013-2014 Agustin Cruz openpyme.mx
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .currency_getter_interface import CurrencyGetterInterface
from datetime import datetime
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

import logging
_logger = logging.getLogger(__name__)


class NI_BCNGetter(CurrencyGetterInterface):
    """Implementation of Currency_getter_factory interface
    for Banco Central de Nicaragua / Central Bank of Nicaragua service

    """
    code = 'NI_BCN'
    name = 'Central Bank of Nicaragua'
    supported_currency_array = [
        "NIO", "EUR", "USD"]

    def rate_retrieve(self):
        """ Get currency exchange from Banxico.xml and proccess it
        TODO: Get correct data from xml instead of process string
        """
        url = ('https://servicios.bcn.gob.ni/Tc_Servicio/ServicioTC.asmx?WSDL')
		
		"""url = ('http://www.banxico.org.mx/rsscb/rss?'
               'BMXC_canal=pagos&BMXC_idioma=es')"""

        from suds.client import Client
        
        logger = logging.getLogger(__name__)
        logger.debug("Bank Nicaragua currency rate service : connecting...")
        client = Client(url)
		dates = datetime.today().now()
		""" Split the date into Year/Month/Day """"
		year= dates.year
		month=dates.month
		day= dates.day
		rate=  client.service.RecuperaTC_Dia(year,month,day)
		logger.debug("Bank Nicaragua sent a valid XML file")
		
		""""rawfile = self.get_url(url)
           dom = parse(StringIO(rawfile))
           value = dom.getElementsByTagName('cb:value')[0]
		   rate = value.firstChild.nodeValue"""

        return float(rate)

    def get_updated_currency(self, currency_array, main_currency,
                             max_delta_days=1):
        """implementation of abstract method of Curreny_getter_interface"""
        logger = logging.getLogger(__name__)
        # we do not want to update the main currency
        if main_currency in currency_array:
            currency_array.remove(main_currency)

        # Suported currencies
        suported = ['NIO', 'USD']
        for curr in currency_array:
            if curr in suported:
                # Get currency data
                main_rate = self.rate_retrieve()
                if main_currency == 'NIO':
                    rate = 1 / main_rate
                else:
                    rate = main_rate
            else:
                # No other currency supported
                continue

            self.updated_currency[curr] = rate
            logger.debug("Rate retrieved from Bank of Nicaragua: 1 %s = %s %s -- Inverse Convertion 1 %s = %s %s" %
                         (curr, main_currency, main_rate, main_currency, curr, rate))
        return self.updated_currency, self.log_info
