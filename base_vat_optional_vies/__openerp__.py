# -*- coding: utf-8 -*-
# License AGPL-3: Tecnativa S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

{
    'name': "Optional validation of VAT via VIES",
    'category': 'Accounting',
    'version': '8.0.1.0.0',
    'depends': [
        'base_vat',
    ],
    'external_dependencies': {
        'python': ['vatnumber'],
    },
    'data': [
        'views/res_partner_view.xml',
    ],
    'author': 'Antiun Ingeniería S.L., '
              'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'http://www.tecnativa.com',
    'license': 'AGPL-3',
    'images': [],
    'installable': True,
}
