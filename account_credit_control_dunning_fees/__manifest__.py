# Copyright 2014-2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{'name': 'Credit control dunning fees',
 'version': '11.0.1.0.0',
 'author': "Camptocamp, Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Accounting',
 'complexity': 'normal',
 'depends': ['account_credit_control'],
 'website': 'https://github.com/OCA/account-financial-tools',
 'data': ['view/policy_view.xml',
          'view/line_view.xml',
          'report/report_credit_control_summary.xml',
          'security/ir.model.access.csv',
          ],
 'installable': True,
 'auto_install': False,
 'license': 'AGPL-3',
 'application': False
 }
