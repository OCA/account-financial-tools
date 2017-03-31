.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========================
Account Journal Lock Date
=========================

Lock each accounting journal independently.

In addition to the lock dates provided by standard Odoo and
account_permanent_lock_move, provide a per journal lock date.

Note: this module depends on account_permanent_lock_move because it
implements stricter checks than standard Odoo, such as verifying that
one cannot create draft moves before the lock date.

Note: the journal lock date is ignored for users that are part of
the Adviser group. This rule can be adapted by overriding method
`_can_bypass_journal_lock_date` of `account.journal`.

Usage
=====

To use this module, you need to set

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/{repo_id}/{branch}

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* a wizard to set the lock date on several journals could be nice to have
* the module does not check that all moves prior the lock date are posted, this could be
  made as part of the wizard

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

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
