# -*- coding: utf-8 -*-
# Copyright 2015-2017 Onestein (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Costcenter',
    'summary': 'Cost center information for invoice lines',
    'author': 'ONESTEiN BV,Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'website': 'http://www.onestein.eu',
    'category': 'Accounting',
    'version': '8.0.1.0.0',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_cost_center.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/account_invoice.xml',
        'views/account_invoice_report.xml',
    ],
    'installable': True,
}
