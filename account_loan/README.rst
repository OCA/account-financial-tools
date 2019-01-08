.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Account Loan management
=======================

This module extends the functionality of accounting to support loans.
It will create automatically moves or invoices for loans.
Moreover, you can check the pending amount to be paid and reduce the debt.

It currently supports two kinds of debts:

* Loans: a standard debt with banks, that only creates account moves.
   Loan types info:
   `APR <https://en.wikipedia.org/wiki/Annual_percentage_rate>`_,
   `EAR <https://en.wikipedia.org/wiki/Effective_interest_rate>`_,
   `Real Rate <https://en.wikipedia.org/wiki/Real_interest_rate>`_.
* Leases: a debt with a bank where purchase invoices are necessary

Installation
============

To install this module, you need to:

#. Install numpy : ``pip install numpy``
#. Follow the standard process

Usage
=====

To use this module, you need to:

#. Go to `Invoicing / Accounting > Adviser > Loans`
#. Configure a loan selecting the company, loan type, amount, rate and accounts
#. Post the loan, it will automatically create an account move with the
   expected amounts
#. Create automatically the account moves / invoices related to loans and
   leases before a selected date

On a posted loan you can:

* Create moves or invoices (according to the configuration)
* Modify rates when needed (only unposted lines will be modified)
* Reduce or cancel the debt of a loan / lease

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://odoo-community.org/logo.png>`_.

Contributors
------------

* Enric Tobella <etobella@creublanca.es>
* Bhavesh Odedra <bodedra@opensourceintegrators.com>

Do not contact contributors directly about support or help with technical issues.

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
