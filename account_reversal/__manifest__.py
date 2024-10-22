# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Reversal",
    "summary": "Account reversal usability improvements",
    "version": "16.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Akretion,"
    "Camptocamp,"
    "ACSONE SA/NV,"
    "Tecnativa,"
    "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_move_view.xml",
        "wizards/account_move_reversal.xml",
    ],
}
