# -*- coding: utf-8 -*-
# Copyright 2016 Serpent Consulting Services Pvt. Ltd
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Credit Control Payment Details",
    "summary": "Account Credit Control Payment Details",
    "version": "8.0.1.0.0",
    "category": "Accounting",
    "description": "Account Credit Control Payment Details",
    'website': 'http://www.serpentcs.com',
    "author": """Serpent Consulting Services Pvt. Ltd.,
                Agile Business Group,
                Odoo Community Association (OCA)""",
    "license": "AGPL-3",
    "depends": [
        "account_credit_control",
    ],
    'data': [
        'views/report_credit_control_summary.xml', ],
    "installable": True,
}
