# -*- coding: utf-8 -*-
# © 2012-2015 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Check Deposit',
    'version': '10.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Manage deposit of checks to the bank',
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com/',
    'depends': [
        'account_accountant',
    ],
    'data': [
        'data/sequence.xml',
        'views/account_deposit_view.xml',
        'views/account_move_line_view.xml',
        'views/account_config_settings.xml',
        'security/ir.model.access.csv',
        'security/check_deposit_security.xml',
        'report/report.xml',
        'report/report_checkdeposit.xml',
    ],
    'installable': True,
    'application': True,
}
