.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

Account Reversal
================

This module adds an action "Reversal" on account moves,
to allow the accountant to create reversal account moves in 2 clicks.
Also add on account entries:

* a checkbox and filter "to be reversed"
* a link between an entry and its reversal entry

Odoo v11c include a similar action (overwritten by this addon), but with less
features, for instance:

* Allowing inheritance
* Options like prefix (for journal entry and journal item), post and reconcile.
* Create a link between the entry and its reversal
* Mark entries to be reversed in the future.

Usage
=====

If you select an entry from Invoicing > Adviser > Journal Entries,
then an action menu 'Reverse Entries' is available. If clicked, then a wizard
allows user to select Reversal Date, Reversal Journal, Prefix, Post and Reconcile.

* If no Reversal Journal is selected, then the same journal is used
* If Post is True, then reversal entry will be posted else it will be leaved
  as a draft entry.
* If Post and Reconcile are True, then all entry lines with reconciled accounts
  of the entry will be reconciled with the reserval entry ones.

There is also a new menu Invoicing > Adviser > Journal Entries to be Reversed
in order to allow tracking entries that must be reserved for any reason.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/11.0


Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Alexis de Lattre (Akretion)
* Guewen Baconnier (Camptocamp)
* Nicolas Bessi (Camptocamp)
* Torvald Bringsvor (Bringsvor Consulting)
* Sandy Carter (Savoir-faire Linux)
* Stéphane Bidoul (ACSONE)
* Antonio Espinosa (Tecnativa)

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
