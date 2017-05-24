# -*- coding: utf-8 -*-
{'name': 'Credit control dunning fees',
 'version': '10.0.1.0.0',
 'author': "Camptocamp, Odoo Community Association (OCA)",
 'maintainer': 'Camptocamp',
 'category': 'Accounting',
 'complexity': 'normal',
 'depends': ['account_credit_control'],
 'website': 'http://www.camptocamp.com',
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
