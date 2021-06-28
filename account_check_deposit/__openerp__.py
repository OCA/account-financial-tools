# -*- coding: utf-8 -*-
###############################################################################
#
#   account_check_deposit for Odoo
#   Copyright (C) 2012-2015 Akretion (http://www.akretion.com/)
#   @author: Benoît GUILLOT <benoit.guillot@akretion.com>
#   @author: Chafique DELLI <chafique.delli@akretion.com>
#   @author: Alexis de Lattre <alexis.delattre@akretion.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
#
###############################################################################

{
    'name': 'Account Check Deposit',
    'version': '9.0.0.1.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Manage deposit of checks to the bank',
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com/',
    'depends': [
        'account_accountant',
    ],
    'data': [
        'views/account_deposit_view.xml',
        'views/account_move_line_view.xml',
        'data/account_deposit_sequence.xml',
        'views/company_view.xml',
        'security/ir.model.access.csv',
        'security/check_deposit_security.xml',
        'data/account_data.xml',
        'report/report.xml',
        'report/report_checkdeposit.xml',
    ],
    'installable': True,
    'application': True,
}
