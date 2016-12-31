# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Open Invoices Reports",
    "summary": "Open Invoices Reports",
    "version": "8.0.1.0.0",
    "category": "Accounting",
    'website': 'http://www.serpentcs.com',
    "author": """Serpent Consulting Services Pvt. Ltd.,
                Agile Business Group,
                Odoo Community Association (OCA)""",
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    'data': [
        'views/res_company_view.xml',
        'views/report_open_invoices_view.xml',
        'views/report_paperformat.xml',
    ],
    "installable": True,
}
