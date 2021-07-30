# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Account documents direct scan",
    'version': '11.0.1.0.0',
    'category': 'Accounting',
    "author": "Rosen Vladimirov <vladimirov.rosen@gmail.com>, "
              "dXFactory Ltd. <http://www.dxfactory.eu>",
    'website': 'https://github.com/OCA/account-financial-tools',
    'license': 'AGPL-3',
    "depends": [
            'account_documents',
            'base_scanner_access',
            ],
    'data': [
            'wizards/scanning_document_wizard.xml',
            'views/ir_attachment_view.xml',
            ],
    'installable': True,
}
