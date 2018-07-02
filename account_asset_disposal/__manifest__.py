# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2017 Tecnativa - Luis M. Ontalba
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account asset disposal",
    "summary": "Makes asset close account move automatically",
    "version": "10.0.2.0.0",
    "category": "Accounting & Finance",
    "website": "http://github.com/OCA/account-financial-tools",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "account_asset",
    ],
    "data": [
        "views/account_asset_asset_views.xml",
        "views/account_asset_category_views.xml",
        "wizards/account_asset_disposal_wizard_view.xml",
    ],
}
