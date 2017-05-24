.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================
Credit control dunning fees
===========================

This module extends the functionality of account_credit_control to add
the notion of dunning fees on credit control lines.

Installation
============

Just install it.

Configuration
=============

You can specifiy a fixed fees amount, a product and a currency
on the credit control level form.

The amount will be used as fees values the currency will determine
the currency of the fee. If the credit control line has not the
same currency as the fees currency, fees will be converted to
the credit control line currency.

The product is used to compute taxes in reconciliation process.

.. figure:: path/to/local/image.png
   :alt: alternative description
   :width: 600 px

Usage
=====

Fees are automatically computed on credit run and saved
on the generated credit lines.

Fees can be manually edited as long credit line is draft

Credit control Summary report includes a new fees column:
Support of fees price list

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Nicolas Bessi (Camptocamp)
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Adrien Peiffer (acsone)
* Akim Juillerat <akim.juillerat@camptocamp.com>

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
