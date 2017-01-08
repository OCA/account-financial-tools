.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Currency Rate Update
====================

Import exchange rates from the Internet.

The module is able to use the following sources:

1. Admin.ch
   Updated daily, source in CHF.

2. European Central Bank (ported by Grzegorz Grzelak - OpenGLOBE.pl)
   The reference rates are based on the regular daily query
   procedure between central banks within and outside the European
   System of Central Banks, which normally takes place at 2.15 p.m.
   (14:15) ECB time. Source in EUR.
   http://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html

3. Yahoo Finance
   Updated daily

4. Polish National Bank (Narodowy Bank Polski) (by Grzegorz Grzelak - OpenGLOBE.pl)
   Takes official rates from www.nbp.pl. Adds rate table symbol in log.
   You should check when rates should apply to bookkeeping.
   If next day you should change the update hour in schedule settings
   because in Odoo they apply from date of update (date - no hours).

5. Banxico for USD & MXN (created by Agustín Cruz)
   Updated daily

6. Bank of Canada - noon rates (by Daniel Dico - OERP Canada)
   Using RSS feeds from: http://www.bankofcanada.ca/rss-feeds/
   Updated daily (except weekends and holidays).
   Noon and Closing rates available - this module is using the noon rates.

7. National Bank of Romania (Banca Nationala a Romaniei)

Configuration
=============

The update can be set under the company form.
You can set for each services which currency you want to update.
The logs of the update are visible under the service note.
You can active or deactivate the update.
The module uses internal ir-cron feature from Odoo, so the job is
launched once the server starts if the 'first execute date' is before
the current day.

Usage
=====

The module supports multi-company currency in two ways:

* when currencies are shared, you can set currency update only on one
  company
* when currencies are separated, you can set currency on every company
  separately

A function field lets you know your currency configuration.

If in multi-company mode, the base currency will be the first company's
currency found in database.

Know issues / Roadmap
=====================

Roadmap:
* Google Finance.
* Updated daily from Citibank N.A., source in EUR. Information may be delayed.
  This is parsed from an HTML page, so it may be broken at anytime.


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

* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* JB Aubort
* Grzegorz Grzelak <grzegorz.grzelak@openglobe.pl> (ECB, NBP)
* Alexis de Lattre <alexis@via.ecp.fr>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com> (Port to V7)
* Agustin Cruz <openpyme.mx> (BdM)
* Dorin Hongu <dhongu@gmail.com> (BNR)
* Fekete Mihai <feketemihai@gmail.com> (Port to V8)
* Daniel Dico <dd@oerp.ca> (BoC)

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
