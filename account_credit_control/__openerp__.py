# -*- coding: utf-8 -*-
# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
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
<<<<<<< c22b2dde9403c91dc4e4f0835f97c737e54bdb43:account_credit_control/__openerp__.py
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
 'installable': False,
=======
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
 'demo': [
 ],
 'installable': True,
>>>>>>> account_credit_control: remove demo file.:account_credit_control/__manifest__.py
 'license': 'AGPL-3',
 'application': True
 }
