.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License

Currency Rate Update NBRM
=========================

This module is an extension of the original module Currency Rate Update.
This module import exchange rates from  National Bank of the Republic of Macedonia.


Configuration
=============

The update can be set under the company form.
You can set for each services which currency you want to update.
The logs of the update are visible under the service note.
You can active or deactivate the update.
The module uses internal ir-cron feature from Odoo, so the job is
launched once the server starts if the 'first execute date' is before
the current day.

External Dependencies
=====================
* PySimpleSOAP is used as SOAP library for communication to the NBRM service. It can be installed with pip (``pip install pysimplesoap``)


Usage
=====

The module supports multi-company currency in two ways:

* when currencies are shared, you can set currency update only on one
  company
* when currencies are separated, you can set currency on every company
  separately

A function field lets you know your currency configuration.

If in multi-company mode, the base currency will be the first company's
currency found in database.

Know issues / Roadmap
=====================
Please check the basic module for issues related with it.


Credits
=======

Contributors
------------
* Darko Nikolovski <darko@versada.eu>

Please check the basic module for the list of its contributors.


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
