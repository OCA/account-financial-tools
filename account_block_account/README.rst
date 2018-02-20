.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: https://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

================
Blocked accounts
================

This module was written to allow financial managers to block certain (general or analytic) accounts for any accounting action. The result is that said accounts will be available in the system, but not selectable for any bookkeeping action.

Configuration
=============

To configure this module, you need to:

#. go to some account and set the `Blocked` flag
#. trying to use said account on any invoice, invoice line, move or move line will raise

Usage
=====

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
    :alt: Try me on Runbot
    :target: https://runbot.odoo-community.org/runbot/92/8.0

Known issues / Roadmap
======================

* there'll be a plethora of other models where the blocking must be implemented in order to have a consistent user experience here
* a group that is allowed to override blocks might be useful

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

* Holger Brunn <hbrunn@therp.nl>

Do not contact contributors directly about help with questions or problems concerning this addon, but use the `community mailing list <mailto:community@mail.odoo.com>`_ or the `appropriate specialized mailinglist <https://odoo-community.org/groups>`_ for help, and the bug tracker linked in `Bug Tracker`_ above for technical issues.

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
