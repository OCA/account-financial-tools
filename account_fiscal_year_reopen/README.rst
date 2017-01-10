.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

==================
Reopen Fiscal Year
==================

This module allows to reopen a fiscal year after it has been closed.

Odoo advises to make a back-up of a database before closing a fiscal year, and
to restore the database if the user regrets this decision. This is not a real
solution as on restore all changes to the database made in the meantime will
be lost.

Of course a fiscal year can easily be reopened by resetting the state of the
fiscal year to 'draft' using a postgress client like psql. This solution is
dependant on system administrators. This module gives the possibility to
financial managers. (Of course the sysadmin still needs to install this
module ;-)).

Configuration
=============

No special configuration is needed for this module.

Known issues
============

None.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_fiscal_year_reopen%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------
- Ronald Portier (Therp BV)

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
