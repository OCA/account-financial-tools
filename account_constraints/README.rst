.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================
Account Constraints
===================

Add constraints in the accounting module of OpenERP to avoid bad usage
by users that lead to corrupted datas. This is based on our experiences
and legal state of the art in other software.

Summary of constraints are:

* Add a constraint on account move: you cannot pickup a date that is not
  in the fiscal year of the concerned period (configurable per journal)

* For manual entries when multicurrency:

  a. Validation on the use of the 'Currency' and 'Currency Amount'
     fields as it is possible to enter one without the other
  b. Validation to prevent a Credit amount with a positive
     'Currency Amount', or a Debit with a negative 'Currency Amount'

* Add a check on entries that user cannot provide a secondary currency
  if the same than the company one.

* Remove the possibility to modify or delete a move line related to an
  invoice or a bank statement, no matter what the status of the move
  (draft, validated or posted). This is useful in a standard context but
  even more if you're using `account_default_draft_move`. This way you ensure
  that the user cannot make mistakes even in draft state, he must pass through
  the parent object to make his modification.

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

* Stéphane Bidoul <stephane.bidoul@acsone.eu>


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
