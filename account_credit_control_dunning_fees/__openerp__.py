# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
{'name': 'Credit control dunning fees',
 'version': '0.1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Accounting',
 'complexity': 'normal',
 'depends': ['account_credit_control'],
 'description': """
Dunning Fees for Credit Control
===============================

This extention of credit control adds the notion of dunning fees
on credit control lines.

Configuration
-------------
For release 0.1 only fixed fees are supported.

You can specifiy a fixed fees amount, a product and a currency
on the credit control level form.

The amount will be used as fees values the currency will determine
the currency of the fee. If the credit control line has not the
same currency as the fees currency, fees will be converted to
the credit control line currency.

The product is used to compute taxes in reconciliation process.

Run
---
Fees are automatically computed on credit run and saved
on the generated credit lines.

Fees can be manually edited as long credit line is draft

Credit control Summary report includes a new fees column.
-------
Support of fees price list

""",
 'website': 'http://www.camptocamp.com',
 'data': ['view/policy_view.xml',
          'view/line_view.xml',
          'report/report.xml'],
 'demo': [],
 'test': [],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False}
