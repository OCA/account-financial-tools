Adds a wizard to update a company account chart from a chart template.
======================================================================

This is a pretty useful tool to update Odoo installations after tax reforms
on the official charts of accounts, or to apply fixes performed on the chart
template.

The wizard:

* Allows the user to compare a chart and a template showing differences
  on accounts, taxes, tax codes and fiscal positions.
* It may create the new account, taxes, tax codes and fiscal positions detected
  on the template.
* It can also update (overwrite) the accounts, taxes, tax codes and fiscal
  positions that got modified on the template.

Usage
=====

The wizard, accesible from *Accounting > Configuration > Accounts > Update
chart of accounts*, lets the user select what kind of objects must
be checked/updated, and whether old records must be checked for changes and
updates.

It will display all the objects to be created / updated with some information
about the detected differences, and allow the user to exclude records
individually.

Credits
=======

Contributors
------------

* Jordi Esteve
* Borja López Soilán
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
* Joaquín Gutierrez <joaquingpedrosa@gmail.com>
* invitu
* Stéphane Bidoul <stephane.bidoul@acsone.eu>
* Antonio Espinosa <antonioea@antiun.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
