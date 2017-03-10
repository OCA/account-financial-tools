# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Payment Follow-up Management',
    'version': '9.0.1.0.0',
    'category': 'Accounting & Finance',
    'author': 'Odoo SA, '
              'Tecnativa, '
              'Odoo Community Association (OCA),',
    'license': 'AGPL-3',
    'website': 'https://www.odoo.com/',
    'depends': [
        'account',
        'mail'
    ],
    'data': [
        'security/account_followup_security.xml',
        'security/ir.model.access.csv',
        'report/account_followup_report.xml',
        'wizards/account_followup_view.xml',
        'wizards/account_followup_print_view.xml',
        'data/account_followup_data.xml',
        'views/account_followup_customers.xml',
        'views/res_config_view.xml',
        'views/report_followup.xml',
        'views/account_followup_reports.xml',
    ],
    'demo': [
        'demo/account_followup_demo.xml'
    ],
    'installable': True,
    'auto_install': False,
}
