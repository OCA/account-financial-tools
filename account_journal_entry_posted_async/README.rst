.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Account Journal Async Entry Posted
==================================

This module add a new checkbox on the journal to post asynchronously entries
created for the journal without any manual validation.

In this module we take advantage of the queue and channel system from Odoo
Connector to sequentially post entries in background and therefore avoid 
concurrent updates on ir_sequence when the system is intensely used. 

Installation
============

Connector jobs are created in a channel named
*root.account_move_validate*. The channel must be configured with a
capacity of 1::

     ODOO_CONNECTOR_CHANNELS=root:X,root.account_move_validate:1

See the `connector documentation
<http://odoo-connector.com/guides/jobrunner.html>`_ to see how to configure
the capacity of channels .

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_journal_entry_posted_async%0Aversion:%20{version}%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Contributors
------------

* Laurent Mignon <laurent.mignon@acsone.eu>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
