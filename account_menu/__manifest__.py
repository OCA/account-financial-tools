# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account - Missing Menus',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': "Adds missing menu entries for Account module",
    'author': "GRAP, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': [
        'account',
        'account_coa_menu',
        'account_group_menu',
        'account_tag_menu',
        'account_type_menu',
    ],
    'data': [
        'views/menu.xml',
        'views/view_account_bank_statement.xml',
    ],
    'demo': [
        'demo/res_groups.xml',
    ],
    'installable': True,
}
