.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===========================================================
Detect changes and update the Account Chart from a template
===========================================================

This is a pretty useful tool to update Odoo installations after tax reforms
on the official charts of accounts, or to apply fixes performed on the chart
template.

The wizard:

* Allows the user to compare a chart and a template showing differences
  on accounts, taxes, tax codes and fiscal positions.
* It may create the new account, taxes, tax codes and fiscal positions detected
  on the template.
* It can also update (overwrite) the accounts, taxes, tax codes and fiscal
  positions that got modified on the template.

Usage
=====

The wizard, accesible from *Accounting > Configuration > Settings > Chart of
Accounts > Update chart of accounts*, lets the user select what kind of objects
must be checked/updated, and whether old records must be checked for changes
and updates.

It will display all the objects to be created / updated with some information
about the detected differences, and allow the user to exclude records
individually.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/9.0

Known issues / Roadmap
======================

* Add tests.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble,
please check there if your issue has already been reported. If you spotted it
first, help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Jairo Llopis <jairo.llopis@tecnativa.com>
* Jacques-Etienne Baudoux <je@bcim.be>
* Sylvain Van Hoof <sylvain@okia.be>

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
