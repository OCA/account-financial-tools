# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{'name': 'Account Credit Control',
 'version': '10.0.1.4.4',
 'author': "Camptocamp,Odoo Community Association (OCA),Okia",
 'maintainer': 'Camptocamp',
 'category': 'Finance',
 'depends': [
     'base',
     'account',
     'mail',
 ],
 'website': 'https://www.camptocamp.com',
 'data': [
     "security/res_groups.xml",
     # Reports
     "report/report.xml",
     "report/report_credit_control_summary.xml",

     # Data
     "data/data.xml",

     # Views
     "views/account_invoice.xml",
     "views/credit_control_line.xml",
     "views/credit_control_policy.xml",
     "views/credit_control_run.xml",
     "views/res_company.xml",
     "views/res_partner.xml",

     # Wizards
     "wizard/credit_control_emailer_view.xml",
     "wizard/credit_control_marker_view.xml",
     "wizard/credit_control_printer_view.xml",
     "wizard/credit_control_policy_changer_view.xml",

     # Security
     "security/ir.model.access.csv",
 ],
 'installable': True,
 'license': 'AGPL-3',
 'application': True
 }
