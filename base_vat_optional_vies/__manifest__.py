# -*- coding: utf-8 -*-
# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2016 Tecnativa - Sergio Teruel
# Copyright 2017 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Optional validation of VAT via VIES",
    'category': 'Accounting',
    'version': '10.0.1.0.0',
    'depends': [
        'base_vat',
    ],
    'external_dependencies': {
        'python': ['vatnumber'],
    },
    'data': [
        'views/res_partner_view.xml',
    ],
    'author': 'Tecnativa,'
              'Odoo Community Association (OCA)',
    'website': 'https://www.tecnativa.com',
    'license': 'AGPL-3',
    'installable': True,
}
