# Copyright 2014-2022 Acsone (http://acsone.eu).
# Copyright 2016-2022 Akretion France (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2018-2022 DynApps (https://odoo.dynapps.be/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Partner Required",
    "version": "17.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Adds an option 'partner policy' on accounts",
    "author": "ACSONE SA/NV,Akretion,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": ["views/account_account.xml"],
    "installable": True,
    "application": False,
}
