# Copyright 2019 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Account Lock To Date and Res Config',
    'summary': """
        Allows to set an account lock date in the future.""",
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Eficent, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'installable': True,
    'depends': [
        'account_lock_to_date',
    ],
    'data': [
        'views/res_config_settings_views.xml',
    ],
}
