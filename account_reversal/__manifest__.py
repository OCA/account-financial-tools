# Copyright 2011 Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2012-2013 Guewen Baconnier (Camptocamp)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Reversal",
    "summary": "Wizard for creating a reversal account move",
    "version": "11.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://odoo-community.org/",
    "author": "Akretion,"
              "Camptocamp,"
              "ACSONE SA/NV,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account"
    ],
    "data": [
        "wizard/account_move_reverse_view.xml",
        "views/account_move_view.xml",
    ],
}
