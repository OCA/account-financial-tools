# Copyright 2019 Avoin.Systems
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Multipartner Bank Account",
    "summary": "Allow multiple partners to have the same bank account number",
    "version": "11.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Avoin.Systems, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
    ],
    "data": [
        "views/partner_bank_views.xml",
    ],
}
