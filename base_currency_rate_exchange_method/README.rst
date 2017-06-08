.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Currency Exchange Rate Method
=============================

Allow company to choose between (1) direct exchange rate method, 
and (2) indirect exchange rate method

Direct Method:
With the direct method of foreign exchange quotation, the exchange rate is expressed as the 
number of units of the domestic currency needed to acquire one (1.0) unit of the 
pertinent foreign currency. Within the U.S., this method is also referred to 
as quoting exchange rates in American (U.S.) terms.

Indirect Method:
With the indirect method of foreign exchange quotation, the exchange rate is expressed 
as the number of units of the pertinent foreign currency needed to acquire 
one (1.0) unit of the domestic currency. In the U.S., this method is 
referred to as quoting the exchange rate in foreign terms.

http://www.investopedia.com/exam-guide/cfa-level-1/global-economic-analysis/foreign-exchange.asp

Configuration
=============

Exchange rate method can be set under company form


Usage
=====

The exchange rate mtehod will affect the way you input currency rate
e.g:

* Given company currency equal is USD (USD = 1.0)
* Suppose you are given the direct quote, in U.S. terms, between the U.S. dollar and the euro as:
  1 EUR = 1.2830 USD
* If you use indirect method than You should input EUR rate: 1 / 1.2830 = 0.779423227
  If you use direct method than you should input EUR rate: 1.2830


Know issues / Roadmap
=====================



Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20currency_rate_update%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Andhitia Rama <andhitia.r@gmail.com>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
