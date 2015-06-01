.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Account chart reset
===================

Adds a method to the company to remove its chart of accounts, including all
related transactions, journals etc. By necessity, this process also removes
the company's bank accounts as they are linked to the company's journals and
the company's payment orders and payment modes if the payment module is
installed.

As a result, you can then reconfigure the company chart of account with the
same or a different chart template.

Usage
=====

To prevent major disasters when this module is installed, no interface is
provided. Please run through xmlrpc, for instance using erppeek: ::

    import erppeek
    
    host = 'localhost'
    port = '8069'
    admin_pw = 'admin'
    dbname = 'openerp'
    
    client = erppeek.Client('http://%s:%s' % (host, port))
    client.login('admin', admin_pw, dbname)
    client.execute('res.company', 'reset_chart', 1)

Known issues / Roadmap
======================

This should work with the standard accounting modules installed. All sorts of
combinations with third party modules are imaginable that would require
modifications or extensions of the current implementation.

Sequences are not reset during the process.


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/account-financial-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/account-financial-tools/issues/new?body=module:%20account_reset_chart%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Stefan Rijnhart <stefan@therp.nl>

Icon courtesy of Alan Klim (CC-BY-20) -
https://www.flickr.com/photos/igraph/6469812927/

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
