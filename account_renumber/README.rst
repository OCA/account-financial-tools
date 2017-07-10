.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Account Renumber Wizard
=======================

This module extends the functionality of accounting to allow the accounting
manager to renumber account moves by date only for admin.

The wizard, which is accesible from the "End of Period" menuitem,
lets you select journals, periods, and a starting number. When
launched, it renumbers all posted moves that match selected criteria
(after ordering them by date).

It will recreate the sequence number for each account move
using its journal sequence, which means that:

- Sequences per journal are supported.
- Sequences with prefixes and suffixes based on the move date are also
  supported.

Usage
=====

To use this module, you need to:

#. Be an accounting manager.
#. Go to *Accounting > Adviser > Renumber journal entries*.
#. Choose the *First number* of the journal entry that you want. It will be
   used to start numbering from there on.
#. Choose the *Starting date* and *Ending date*, to set when you want the
   process to begin and end.
#. Choose the journals where you want to perform the renumberings.
#. Press *Renumber*.

Now, the wizard will locate all journal entries found in those journals and
dates, and start numbering them without gaps in a sequential order that starts
with the *First number* you chose and matches the entry date order.

If no matches are found, you will be alerted. Otherwise, you will be redirected
to a view of all the entries that have been renumbered.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble,
please check there if your issue has already been reported. If you spotted it
first, help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Pedro M. Baeza <pedro.baeza@tecnativa.com>
* Jordi Llinares
* Joaquín Gutiérrez <http://www.gutierrezweb.es>
* Jairo Llopis <jairo.llopis@tecnativa.com>
* David Vidal <david.vidal@tecnativa.com>

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
