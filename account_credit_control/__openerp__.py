# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012 Camptocamp SA
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
{'name': 'Account Credit Control',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Finance',
 'complexity': "normal",
 'depends': ['base', 'account',
             'email_template', 'report_webkit'],
 'description': """
Credit Control
==============

Configuration
-------------

Configure the policies and policy levels in ``Accounting  > Configuration >
Credit Control > Credit Policies``.
You can define as many policy levels as you need.

Configure a tolerance for the Credit control and a default policy
applied on all partners in each company, under the Accounting tab.

You are able to specify a particular policy for one partner or one invoice.

Usage
-----

Menu entries are located in ``Accounting > Periodical Processing > Credit
Control``.

Create a new "run" in the ``Credit Control Run`` menu with the controlling date.
Then, use the ``Compute credit lines`` button. All the credit control lines will
be generated. You can find them in the ``Credit Control Lines`` menu.

On each generated line, you have many choices:
 * Send a email
 * Print a letter
 * Change the state (so you can ignore or reopen lines)
 """,
 'website': 'http://www.camptocamp.com',
 'data': ["report/report.xml",
          "data.xml",
          "line_view.xml",
          "account_view.xml",
          "partner_view.xml",
          "policy_view.xml",
          "run_view.xml",
          "company_view.xml",
          "wizard/credit_control_emailer_view.xml",
          "wizard/credit_control_marker_view.xml",
          "wizard/credit_control_printer_view.xml",
          "security/ir.model.access.csv"],
 'demo_xml': ["credit_control_demo.xml"],
 'tests': [],
 'installable': True,
 'license': 'AGPL-3',
 'application': True
 }
