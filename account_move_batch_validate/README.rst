Account Move Batch Validate
===========================

This module provides a wizard to post many Journal Entries in batch. it
uses the queue system introduced by the OpenERP Connector to handle a
big quantity of moves in batch.

The module account_default_draft_move introduces a workflow where the
Journal Entries are always entered in OpenERP in draft state, and the
posting happens later, for example at the end of the period. The core
account module provides a wizard to post all the moves in the period,
but that is problematic when there are many moves.

The posting of a move takes some time, and doing that synchronously,
in one transaction is problematic.

In this module, we leverage the power of the queue system of the
OpenERP Connector, that can be very well used without other concepts
like Backends and Bindings.

This approach provides many advantages, similar to the ones we get
using that connector for e-commerce:

- Asynchronous: the operation is done in background, and users can
  continue to work.
- Dedicated workers: the queued jobs are performed by specific workers
  (processes). This is good for a long task, since the main workers are
  busy handling HTTP requests and can be killed if operations take
  too long, for example.
- Multiple transactions: this is an operation that doesn't need to be
  atomic, and if a line out of 100,000 fails, it is possible to catch
  it, see the error message, and fix the situation. Meanwhile, all
  other jobs can proceed.

Credits
=======

Contributors
------------

* Leonardo Pistone <leonardo.pistone@camptocamp.com>
* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Rudolf Schnapka <rs@techno-flex.de>
* Stéphane Bidoul (ACSONE) <stephane.bidoul@acsone.eu>
* Adrien Peiffer (ACSONE) <adrien.peiffer@acsone.eu>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose mission is to support the collaborative development of Odoo features and promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.