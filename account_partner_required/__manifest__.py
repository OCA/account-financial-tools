# Copyright 2014-2020 Acsone (http://acsone.eu).
# Copyright 2016-2020 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2018-2020 DynApps (https://odoo.dynapps.be/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account partner required",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Adds an option 'partner policy' on account types",
    "author": "ACSONE SA/NV,Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account_menu",
    ],
    "data": [
        "views/account_account.xml",
        "views/account_account_type.xml",
    ],
    "installable": True,
    "application": False,
}
