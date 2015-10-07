# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Eficent (<http://www.eficent.com/>)
#              <contact@eficent.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Account Voucher Number to Move",
    "version": "0.1",
    "license": "AGPL-3",
    "author": "Eficent",
    "website": "www.eficent.com",
    "category": "'Accounting & Finance",
    "depends": ["account_voucher"],
    "description": """
Account Voucher Number to Move
==============================
This module extend the Vouchers so that any change made to the voucher
number is copied to the Account Move's reference field.

This is going to be useful in checks, where the check number is usually
entered manually to the system once it has been printed, for reference
purposes.


Installation
============

No additional installation instructions are required.


Configuration
=============

This module does not require any additional configuration.

Usage
=====

No specific usage instructions are required.

Known issues / Roadmap
======================

Credits
=======

Contributors
------------

* Jordi Ballester <jordi.ballester@eficent.com>


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
    """,
    "init_xml": [],
    "update_xml": [],
    'demo_xml': [],
    'test': [],
    'installable': True,
    'active': False,
    'certificate': '',
}
