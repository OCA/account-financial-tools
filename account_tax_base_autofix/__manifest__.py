# © 2019 dXFactory Ltd. (<http://www.dxfactory.eu>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Account Tax base autofix',
    'version': '11.0.0.1.0',
    'license': 'AGPL-3',
    'author': "Rosen Vladimirov, dXFactory Ltd., "
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'category': 'Accounting',
    'depends': [
        'account',
    ],
    'data': [
        'wizards/permanent_taxbase_autofix.xml',
    ],
    'demo': [],
    'installable': True,
}
