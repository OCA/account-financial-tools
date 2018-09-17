# -*- coding: utf-8 -*-
# Copyright 2015 Domatix Technologies  S.L. (http://www.domatix.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Account Reconcile Trace',
    'version': '8.0.1.0.0',
    'category': 'Account',
    'license': 'AGPL-3',
    'author': 'Domatix,Odoo Community Association (OCA)',
    'website': 'http://www.domatix.com',
    'depends': ['account'],
    'demo': [
        'demo/account_reconcile_trace_demo.xml',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_view.xml',
    ],
    'installable': True,
}
