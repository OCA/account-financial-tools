# © 2014-2016 Acsone (http://acsone.eu).
# © 2016 Akretion (http://www.akretion.com/)
# @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
# @author Alexis de Lattre <alexis.delattre@akretion.com>
# © 2018 DynApps (https://odoo.dynapps.be/)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account partner required",
    "version": "11.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Adds an option 'partner policy' on account types",
    "author": "ACSONE SA/NV,Akretion,Odoo Community Association (OCA)",
    "website": "http://acsone.eu/",
    "depends": [
        "account_type_menu",
    ],
    "data": [
        "views/account.xml",
    ],
    "installable": True,
    "application": False,
}
