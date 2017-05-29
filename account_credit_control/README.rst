.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==============
Credit Control
==============

Installation
============

Just install it

Configuration
=============

Configure the policies and policy levels in ``Accounting  > Configuration >
Credit Control > Credit Control Policies``.
You can define as many policy levels as you need.

Configure a tolerance for the Credit control and a default policy
applied on all partners in each company, under the Accounting tab.

You are able to specify a particular policy for one partner or one invoice.

Usage
=====

Menu entries are located in ``Accounting > Adviser > Credit Control``.

Create a new "run" in the ``Credit Control Run`` menu with the controlling date.
Then, use the ``Compute Credit Lines`` button. All the credit control lines will
be generated. You can find them in the ``Credit Control Lines`` menu.

On each generated line, you have many choices:
 * Send a email
 * Print a letter
 * Change the state (so you can ignore or reopen lines)


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
* Guewen Baconnier (Camptocamp)
* Sylvain Van Hoof (Okia SPRL) <sylvain@okia.be>
* Akim Juillerat (Camptocamp <akim.juillerat@camptocamp.com>

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
