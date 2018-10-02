# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Tag Menu',
    'version': '12.0.1.0.0',
    'category': 'Accounting',
    'license': 'AGPL-3',
    'summary': "Adds a menu entry for Account Tags",
    'author': "Forest and Biomass Romania, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'depends': ['account'],
    'data': ['views/account_tag.xml'],
    'demo': ['demo/account_tax_tags.xml',
             'demo/account_tax_data.xml'],
    'installable': True,
}
