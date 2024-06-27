# -*- coding: utf-8 -*-
# Copyright 2012-2016 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Check Deposit',
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Manage deposit of checks to the bank',
    'author': "Akretion,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': 'http://github.com/OCA/account-financial-tools',
    'depends': [
        'account_invoicing',
    ],
    'development_status': 'Mature',
    'data': [
        'data/sequence.xml',
        'views/account_deposit_view.xml',
        'views/account_move_line_view.xml',
        'views/res_config_settings_views.xml',
        'security/ir.model.access.csv',
        'security/check_deposit_security.xml',
        'report/report.xml',
        'report/report_checkdeposit.xml',
    ],
    'installable': True,
}
