# Copyright 2012-2016 Akretion (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Bank Receipt',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': 'Manage deposit of checks to the bank',
    'author': "Odoo Community Association (OCA),"
              "Akretion,"
              "Tecnativa",
    'website': 'https://github.com/OCA/account-financial-tools/tree/12.0/'
               'account_bank_receipt',
    'depends': [
        'account',
    ],
    'development_status': 'Mature',
    'data': [
        'security/ir.model.access.csv',
        'security/bank_receipt_security.xml',
        'data/sequence.xml',
        'views/account_bank_receipt_view.xml',
        'views/res_config_settings_views.xml',
        'report/report.xml',
        'report/report_checkdeposit.xml',
    ],
    'installable': True,
}
