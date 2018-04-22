.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3


==============
Account Storno
==============

This module adds the posibility to use Storno Accounting, a business practice
commonly used in Eastern European countries.

Storno accounting is a practice of using negative debit or credit amounts
to reverse original journal account entries.
Because bookkeepers typically write Storno entries in red ink,
this accounting practice is also known as Red Storno.

There is a difference between debit turnover and credit turnover,
because the reverse entry makes redundant debit and credit turnover.


Countries where Storno accounting is mandatory or considered as best practice:

* Bosnia and Herzegovina
* China
* Czech Republic
* Croatia
* Poland
* Romania
* Russia
* Serbia
* Slovakia
* Slovenia
* Ukraine

Configuration
=============

To configure this module:

* Go to the menu Accounting/Invoicing > Configuration > Accounting > Journals
* Open in form view the journals for which you want to allow storno 
* Change the value of field Posting policy to "Storno"

Usage
=====

For invoice credit notes you have a new option "Create a storno invoice" in
Refund Policy field, option that copies the invoice in the same journal but
with negative quantities.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Goran Kliska <gkliska@gmail.com>
* Ivan Vađić (Slobodni programi d.o.o.)
* Tomislav Bošnjaković (Storm Computers d.o.o.)
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
