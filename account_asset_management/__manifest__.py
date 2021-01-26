# Copyright 2009-2018 Noviat
# Copyright 2019 Tecnativa - Pedro M. Baeza
# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Assets Management",
    "version": "14.0.1.0.1",
    "license": "AGPL-3",
    "depends": ["account"],
    "excludes": ["account_asset"],
    "external_dependencies": {"python": ["python-dateutil"]},
    "author": "Noviat, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "security/account_asset_security.xml",
        "security/ir.model.access.csv",
        "wizard/account_asset_compute.xml",
        "wizard/account_asset_remove.xml",
        "views/account_account.xml",
        "views/account_asset.xml",
        "views/account_asset_group.xml",
        "views/account_asset_profile.xml",
        "views/account_move.xml",
        "views/account_move_line.xml",
        "views/menuitem.xml",
        "data/cron.xml",
    ],
}
