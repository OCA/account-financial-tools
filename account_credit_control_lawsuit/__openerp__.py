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
{'name': 'Credit Control Lawsuit',
 'version': '0.1',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Accounting',
 'complexity': 'normal',
 'depends': ['base_location',
             'account_credit_control',
             ],
 'website': 'http://www.camptocamp.com',
 'data': ['view/lawsuit_office_view.xml',
          'view/lawsuit_schedule_view.xml',
          'view/credit_control_lawsuit_printer_view.xml',
          'report/report.xml',
          'view/policy_view.xml',
          'view/partner_view.xml',
          'view/account_invoice_view.xml',
          'view/invoice_lawsuit_step_view.xml',
          'report/report_credit_control_lawsuit.xml',
          'data/invoice_lawsuit_step.xml',
          'security/ir.model.access.csv',
          ],
 'demo': [],
 'test': [],
 'installable': True,
 'license': 'AGPL-3',
 }
