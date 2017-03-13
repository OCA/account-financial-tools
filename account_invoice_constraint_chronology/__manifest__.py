# -*- coding: utf-8 -*-
# Copyright 2015-2017 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Invoice Constraint Chronology",
    "version": "10.0.1.0.0",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainer": "ACSONE SA/NV",
    "website": "http://www.acsone.eu",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["account"],
    "description": """
    Account Invoice Constraint Chronology
    This module helps ensuring the chronology of invoice numbers.
    It prevents the validation of invoices when:
    * there are draft invoices with an anterior date
    * there are validated invoices with a posterior date
    """,
    "test": ["../account/test/account_minimal_test.xml"],
    "data": ["view/account_view.xml"],
    'installable': True,
}
