.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=====================
Currency Monthly Rate
=====================

This module extends the functionality of base module to support monthly average
of currency rates.

Installation
============

Just install it.

Usage
=====

To use this module, you need to add the security group 'Monthly currency rates'
to your user, so that a 'Monthly rates' smart button appears on the currency
form view.

In order to compute any amount in another currency using monthly rates, you
only have to pass `monthly_rate=True` in the context of `res.currency.compute`
method :

.. code:: python

    to_amount = from_currency.with_context(monthly_rate=True).compute(from_amount, to_currency)


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0

Known issues / Roadmap
======================

* Monthly currency rates have to be created manually as no automatic updates
  is implemented yet.

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

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Akim Juillerat <akim.juillerat@camptocamp.com>

Do not contact contributors directly about support or help with technical issues.

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
