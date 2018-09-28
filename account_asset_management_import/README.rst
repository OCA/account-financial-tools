.. image:: https://img.shields.io/badge/license-AGPL--3-blue.png
   :target: https://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

===================
Import Fixed Assets
===================

This module allows the import of Fixed Assets from a CSV file.

Before starting the import a number of sanity checks are performed such as:

- check for duplicates
- check if asset profiles are correct

If no issues are found the assets will be loaded.
The resulting Fixed Assets will be in draft mode to allow a final check before confirming the asset.

Usage
=====

Input file column headers
-------------------------

Mandatory Fields
''''''''''''''''

- Reference

  The Reference is checked for uniqueness to avoid loading of duplicate assets.


- Asset Name

- Asset Profile

- Purchase Value

  Purchase Value in Company Currency

- Asset Start Date

  Date format must be yyyy-mm-dd

Other Fields
''''''''''''

Extra columns can be added and will be processed as long as
the column header is equal to the 'ORM' name of the field.
Input fields with no corresponding ORM field will be ignored
unless special support has been added for that field in this
module (or a module that extends the capabilities of this module).

This module has implemented specific support for the following fields:

- Partner

  The value must be unique.
  Lookup logic : exact match on partner reference,
  if not found exact match on partner name.


A blank column header indicates the end of the columns that will be
processed. This allows 'comment' columns on the input lines.

Empty lines or lines starting with '#' will be ignored.

Remark:

If you need to override values from the selected Asset Profile, you should
enter those fields after the 'Asset Profile' field.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/92/10.0

Known Issues
============

This module uses the Python *csv* module for the reading of the input csv file.
The input csv file should take into account the limitations of the *csv* module:

Unicode input is not supported. Also, there are some issues regarding ASCII NUL characters.
Accordingly, all input should be UTF-8 or printable ASCII.
Results are unpredictable when this is not the case.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/account-financial-tools/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Luc De Meyer, Noviat <info@noviat.com>

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
