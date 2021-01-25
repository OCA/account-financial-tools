# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Account documents",
    'version': '11.0.3.0.0',
    'category': 'Accounting',
    "author": "Rosen Vladimirov <vladimirov.rosen@gmail.com>, "
              "dXFactory Ltd. <http://www.dxfactory.eu>",
    'website': 'https://github.com/rosenvladimirov/account-financial-tools',
    'license': 'AGPL-3',
    "depends": [
            'account',
            'sale',
            'purchase',
            ],
    'data': [
            'security/ir.model.access.csv',
            'views/account_invoice_view.xml',
            'views/purchase_views.xml',
            'views/sale_views.xml',
            'views/stock_picking_views.xml',
            'views/account_view.xml',
            'views/ir_attachment_view.xml',
            'views/account_documents_type_views.xml',
            ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
}
