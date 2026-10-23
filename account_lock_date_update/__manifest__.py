# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Lock Date Update",
    "summary": "Update accounting lock dates without access to technical settings",
    "version": "20.0.1.0.0",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "installable": True,
    "depends": ["account"],
    "data": [
        "security/ir.access.csv",
        "wizards/account_update_lock_date.xml",
    ],
}
