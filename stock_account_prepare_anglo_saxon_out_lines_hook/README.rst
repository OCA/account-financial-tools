.. image:: https://img.shields.io/badge/license-AGPLv3-blue.svg
   :target: https://www.gnu.org/licenses/agpl.html
   :alt: License: AGPL-3

=============================
Account Move Anglo Saxon Hook
=============================

This module introduces a hook that allows to customize the criteria why
anglosaxon entries for COGS are created

Standard Odoo will not create those entries for Kits where those are
consumables. But they should be considered because of the interim output
account is hit in the invoice.

References: https://github.com/odoo/odoo/issues/60679
Proposal to Odoo: https://github.com/odoo/odoo/pull/68511

It also introduces a hook in order to add/modify the values on the
anglo saxon journal entries creation. For example, the sales order information


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

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Aaron Henriquez <ahenriquez@forgeflow.com>

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
