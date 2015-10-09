# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2012-2014 Camptocamp SA
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
 'version': '8.0.0.3.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Finance',
 'complexity': "normal",
 'depends': ['base',
             'account',
             'email_template',
             ],
 'website': 'http://www.camptocamp.com',
 'data': ["report/report.xml",
          "report/report_credit_control_summary.xml",
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
          "wizard/credit_control_policy_changer_view.xml",
          "security/ir.model.access.csv"],
 'demo': ["credit_control_demo.xml"],
 'tests': [],
 'installable': True,
 'license': 'AGPL-3',
 'application': True
 }
