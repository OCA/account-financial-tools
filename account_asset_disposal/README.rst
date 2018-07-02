.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

======================
Account asset disposal
======================

This module enables a real asset disposal with the proper accounting entries.

When an asset gets broken or is totally depreciated, you can close it and Odoo
will generate automatically the asset close move (and compute the loss if a
residual value is pending).

You can also cancel this disposal for returning to the previous state.

Configuration
=============

#. Go to *Accounting > Configuration > Management > Asset Types*.
#. There's a new field called "Loss Account" for setting the default loss
   account when disposing assets.

Usage
=====

#. Go to *Accounting > Adviser > Assets*.
#. There you will find a 'Dispose' button (instead of standard 'Set to Close').
#. After clicking it, a wizard pops-up for asking disposal date and loss
   account to use if any residual value is pending.
#. Click on "Dispose asset".
#. A new screen will appear with the disposal account entry.
#. On the asset, all remaining depreciation lines are removed, and a new one
   appears for the disposal move.

You can cancel afterwards the disposal:

#. Click on "Undo disposal" on the asset.
#. The disposal entry is removed.
#. The depreciation board is restored with all the remaining depreciations.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Known issues / Roadmap
======================

* Include a specific message type for notifying the disposal.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Tecnativa (https://www.tecnativa.com):
  * Pedro M. Baeza <pedro.baeza@tecnativa.com>
  * Antonio Espinosa <antonio.espinosa@tecnativa.com>
  * Luis M. Ontalba <luis.martinez@tecnativa.com>

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
