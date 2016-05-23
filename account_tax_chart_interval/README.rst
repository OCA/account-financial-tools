.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Tax chart for a period interval
===============================

Regular tax chart wizard lets you select only one period. With this module,
you can select an initial and ending period, and you will get taxes data
for that interval.

Known issues / Roadmap
======================

* sum_period compute logic has been completely overwritten when coming from
  tax chart wizard because there is no provided hook or facility, so changes
  in the computation upstream (unlikely, but possible) will not be reflected
  with this module.

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
