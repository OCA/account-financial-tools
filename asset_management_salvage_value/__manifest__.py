# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Assets Management Edit Salvage Value',
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'depends': [
        'account_asset_management',
    ],
    'author': "Ecosoft, Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/account-financial-tools',
    'category': 'Accounting & Finance',
    'data': [
        'views/account_asset.xml',
        'wizard/account_asset_salvage_value.xml',
    ],
    'installable': True,
}
