.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=========================
Account Journal Lock Date
=========================

Lock each accounting journal or accounting move independently.

In addition to the lock dates provided by standard Odoo, this module 
provide a journal lock date plus a permanent option.

Note: 
* the journal lock date is ignored for users that are part of
the Adviser group. This rule can be adapted by overriding method
`_can_bypass_journal_lock_date` of `account.journal`.
* if the journal is set at permanent lock, you can use the wizard to 
overwrite the permanency option.

Usage
=====

For locking account moves independently, you have a button available based
on certain conditions: 
* The move in not locked
* The journal is not permanent lock for the move date or the date of the move 
is bigger than journal lock date or company fiscalyear lock date

For locking account journals independently, you need to be an Adviser and go to:
* Accounting -> Adviser -> Actions -> Lock Journal Entries
* Change lock date, add journals that you want to lock, check/uncheck permanency 
lock and click on the Lock button

The wizard will mark all the moves before lock date as 'locked', and will unlock 
the moves after the lock date. There are certain restiction in locking, like 
* you should post account moves before the lock date
* the lock date cannot be lower the company fiscalyear lock date

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0

Known issues / Roadmap
======================


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Benjamin Willig <benjamin.willig@acsone.eu>
* Adrien Peiffer <adrien.peiffer@acsone.eu>
* Vincent Renaville <vincent.renaville@camptocamp.com>
* Akim Juillerat <akim.juillerat@camptocamp.com>
* Matthieu Dietrich <matthieu.dietrich@camptocamp.com>
* Fekete Mihai <feketemihai@gmail.com>

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
