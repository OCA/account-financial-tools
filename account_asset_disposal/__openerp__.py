# -*- coding: utf-8 -*-
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account asset disposal",
    "summary": "Makes asset close account move automatically",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "http://www.tecnativa.com",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_asset",
    ],
    "data": [
        "views/account_asset_asset_view.xml",
        "wizards/account_asset_disposal_wizard_view.xml",
    ],
}
