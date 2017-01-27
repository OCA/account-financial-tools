.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Credit Control
==============

Configuration
-------------

Configure the policies and policy levels in ``Accounting  > Configuration >
Credit Control > Credit Policies``.
You can define as many policy levels as you need.

Configure a tolerance for the Credit control and a default policy
applied on all partners in each company, under the Accounting tab.

You are able to specify a particular policy for one partner or one invoice.

Usage
-----

Menu entries are located in ``Accounting > Periodical Processing > Credit
Control``.

Create a new "run" in the ``Credit Control Run`` menu with the controlling date.
Then, use the ``Compute credit lines`` button. All the credit control lines will
be generated. You can find them in the ``Credit Control Lines`` menu.

On each generated line, use wizard to set lines:
 * ready to be sent
 * ignored

On each line ready to be sent:
 * Send an email
 * Print a letter

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_credit_control%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------
- Guewen Baconnier, Joël Grand-Guillaume, Alexandre Fayolle, Matthieu Dietrich,
  Vincent Renaville, Nicolas Bessi, Yannick Vaucher (Camptocamp)
- Stefan Rijnhart (Therp)
- Adrien Peiffer, Laurent Mignon (Acsone)
- Andrius Preimantas
- Alexis de Lattre, Sebastien Beau (Akretion)
- Thomas Fossoul (Noviat)
- Jacques-Etienne Baudoux (BCIM)

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
