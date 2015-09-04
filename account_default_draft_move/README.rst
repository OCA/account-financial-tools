.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

==============================
Move in draft state by default
==============================

In Odoo there is a flag "Skip draft moves" on accounting journals that controls
if newly created account moves stay in draft state or are posted immediately.
This flag is honored throughout the system except for invoices and
bank statements, for which moves are posted as soon as the documents are
validated. Therefore, to correct errors on invoices and bank statement after
their validation, one is obliged to install the account_cancel module, which in turn
potentially enables the cancellation of all account moves. This is considered
dangerous by some.

To work around this issue, this module does the following:

* It makes sure the flag "Skip draft moves" is always honored, including when
validating invoices and bank statements [1]. This enables different workflows,
such as 1/ the automatic posting of moves coming from some journals (such as
invoices coming from e-commerce), or 2/ moves remaining in draft state, letting
accountants validate them and correct the corresponding invoices before posting
the moves.
* It hides the Cancel button on account moves unless account_cancel is installed
and cancellation is allowed on the corresponding journal. 
* Additionnaly, the Post button is hidden on account moves, therefore providing
a framework where the user work with draft moves until everything is correct,
and validates all account moves at once and the end. [2]

[1] provided the parameter is set in Settings > Configuration, if this
parameter is not set the moves generated from invoices and bank statement
always remain in draft state ignoring the "Skip draft move flag" on
account journal. This parameter is not set by default for backward
compatibility with previous versions of account_default_draft_move.
[2] this behaviour will be made configurable in the near future.

Installation
============

To install this module, you need to:

* Click on install button

Configuration
=============

To configure this module, you need go to:

* Settings > Configuration > Accounting, and configure the checkbox
  "Use journal setting to post journal entries on invoice and 
  bank statement validation" (if not checked, invoice and bank
  statement move stay in draft state).
* On the sale/purchase and bank journals, configure the 
  "Skip draft move flag" to suit your needs.

Usage
=====

For further information, please visit:

* https://www.odoo.com/forum/help-1

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/8.0

For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

* the visibility of the Post button on account moves should be made configurable
  (this module currently hides it unconditionally)
* in 9.0, the parameter should be removed and always honoring the "Skip draft state"
  flag should become the default

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_default_draft_move%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Vincent Renaville <vincent.renaville@camptocamp.com>
* Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
* Joel Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Matthieu Dietrich <matthieu.dietrich@camptocamp.com>
* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Adrien Peiffer <adrien.peiffer@acsone.eu>
* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Rudolf Schnapka <rs@techno-flex.de>
* Laetitia Gangloff <laetitia.gangloff@acsone.eu>

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
