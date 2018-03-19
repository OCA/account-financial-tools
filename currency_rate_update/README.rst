.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Currency Rate Update
====================

Base module to download exchange rates automatically from the Internet.

This module download exchange rates automatically from European central bank service (ported by Grzegorz Grzelak - OpenGLOBE.pl)
The reference rates are based on the regular daily query procedure between central banks within and outside the European System of Central Banks, which normally takes place at 2.15 p.m. (14:15) ECB time. Source in EUR. http://www.ecb.europa.eu/stats/exchange/eurofxref/html/index.en.html

Configuration
=============

To configure the module, go to *Accounting > Configuration > Multi-currencies > Rate Auto-download* and create one or several services to download rates from the Internet.

Then, go to the page *Accounting > Configuration > Settings* and, in the section *Multi Currencies*, make sure that the option *Automatic Currency Rates Download* is enabled.

In developper mode, in the menu *Settings > Technical > Scheduled Actions*, make sure that the action *Currency Rate Update* is active. If you want to run it immediately, use the button *Run Manually*.

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

To fix:

* Bank of Canada

Roadmap:

* Google Finance.
* Updated daily from Citibank N.A., source in EUR. Information may be delayed.
  This is parsed from an HTML page, so it may be broken at anytime.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Jean-Baptiste Aubort <jean-baptiste.aubort@camptocamp.com>
* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Grzegorz Grzelak <grzegorz.grzelak@openglobe.pl> (ECB, NBP)
* Vincent Renaville <vincent.renaville@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com> (Port to V7)
* Agustin Cruz <openpyme.mx> (BdM)
* Jacque-Etienne Baudoux <je@bcim.be>
* Juan Jose Scarafia <jjscarafia@paintballrosario.com.ar>
* Mathieu Benoi <mathben963@gmail.com>
* Fekete Mihai <feketemihai@gmail.com> (Port to V8)
* Dorin Hongu <dhongu@gmail.com> (BNR)
* Paul McDermott
* Alexis de Lattre <alexis@via.ecp.fr>
* Miku Laitinen
* Assem Bayahi
* Daniel Dico <ddico@oerp.ca> (BOC)
* Dmytro Katyukha <firemage.dima@gmail.com>
* Jesús Ventosinos Mayor <jesus@comunitea.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
