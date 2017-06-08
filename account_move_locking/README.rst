.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

====================
Lock journal entries
====================

This module adds the ability to lock journal entries for modification,
based on date ranges.

Usage
=====

In order to lock the journal entries, you need to follow this process:

* You need to post your entry, with the standard wizard Post Journal Entries
  (Invoicing -> Periodic Processing -> Draft Entries -> Post Journal Entries)
* Then, you can use the wizard Lock Date Range
  (Invoicing -> Configuration -> Date ranges -> Lock Date Range)

You can unlock date ranges which are not of the "fiscal year" type, and also
only lock specific journals on each date range.
Locking the date will block every deletion, creation and modification of a
journal entry or journal item (except for reconciliation).

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Vincent Renaville <vincent.renaville@camptocamp.com>
* Matthieu Dietrich <matthieu.dietrich@camptocamp.com>

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
