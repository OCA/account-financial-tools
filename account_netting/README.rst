.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============
AR/AP netting
=============

This module allows to compensate the balance of a receivable account with the
balance of a payable account for the same partner, creating a journal item
that reflects this operation.

**WARNING**: This operation can be forbidden in your country by the accounting
regulations, so you should check current laws before using it. For example, in
Spain, this is not allowed at first instance, unless you document well the
operation from both parties.

Usage
=====

From any account journal entries view:

* Accounting/Journal Entries/Journal Items
* Accounting/Periodic Processing/Reconciliation/Manual Reconciliation

select all the lines that corresponds to both AR/AP operations from the same
partner. Click on "More > Compensate". If the items don't correspond to the
same partner or they aren't AR/AP accounts, you will get an error.

On contrary, a dialog box will be presented with the result of the operation
and a selection of the journal to register the operation. When you click on the
"Compensate" button, a journal entry is created with the corresponding
counterparts of the AR/AP operations.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/8.0

Known issues / Roadmap
======================

* We can add the possibility to pay the netting result amount directly from
  the wizard.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_netting%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


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
