.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

======================
Account Credit Control
======================

Account Credit Control module is a part of Financial Tools used in business to
ensure that once sales are made they are realised as cash. This module helps to
identify outstanding debt beyond tolerance level and setup followup method.

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

Menu entries are located in ``Invoicing > Adviser > Credit Control``.

Create a new "run" in the ``Credit Control Run`` menu with the controlling date.
Then, use the ``Compute Credit Lines`` button. All the credit control lines will
be generated. You can find them in the ``Credit Control Lines`` menu.

On each generated line, you have many choices:
 * Send a email
 * Print a letter
 * Change the state (so you can ignore or reopen lines)
 * Mark a line as Manually Overridden. The line will get the ignored state when a second credit control run is done.
 * Mark one line as Manual followup will also mark all the lines of the partner. The partner will be visible in "Do Manual Follow-ups".


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0

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
* Akim Juillerat (Camptocamp) <akim.juillerat@camptocamp.com>
* Vicent Cubells (Tecnativa) <vicent.cubells@tecnativa.com>
* Kinner Vachhani (Access Bookings Ltd) <kin.vachhani@gmail.com>

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
