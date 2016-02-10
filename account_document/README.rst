.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Account Document
================
Mainly we add to fields to every account.move:

* document_number
* document_type_id

This two fields are going to be computed from other models like invoices, payments, etc.

We decided to use this indepenent number for different reasons:

    1. We do not touch much of odoo (you can install/uninstall this module)
    2. We don't have any constraint to what we need (for eg. we can have two journal entries with same document numbers)
    3. For eg, in argentina, the document number for a Invoice is '0001-00000001' and you can have many invoices with same document number (for eg. for purchases and for eg. for different document types)

TODO

Configuration
=============

TODO

Usage
=====

TODO

Know issues / Roadmap
=====================

TODO

Credits
=======

Contributors
------------

* TODO

Maintainer
----------

.. image:: http://odoo-argentina.org/logo.png
   :alt: Odoo Argentina
   :target: http://odoo-argentina.org

This module is maintained by the Odoo Argentina.

Odoo Argentina, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-argentina.org
