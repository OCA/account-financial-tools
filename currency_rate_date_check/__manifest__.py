# coding: utf-8
# © 2014 Today Akretion
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# @author Mourad EL HADJ MIMOUNE <mourad.elhadj.mimoune@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Currency Rate Date Check',
    'version': '10.0.1.0.0',
    'category': 'Financial Management/Configuration',
    'license': 'AGPL-3',
    'summary': "Make sure currency rates used are always up-to-update",
    'author': "Akretion,Odoo Community Association (OCA)",
    'website': 'http://www.akretion.com',
    'depends': [
        'base',
        'account',
    ],
    'data': [
        'views/company_view.xml',
        'views/account_config_settings.xml',
    ],
    'installable': True,
}
