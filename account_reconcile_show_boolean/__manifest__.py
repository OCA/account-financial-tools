# Copyright 2021 Le Filament (https://le-filament.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "account_reconcile_show_boolean",
    "summary": "Allows to create reconciliable accounts by showing boolean on form view",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Le Filament, Odoo Community Association (OCA)",
    "maintainers": ["remi-filament"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "preloadable": True,
    "depends": [
        "account",
    ],
    "data": [
        "views/account_account_view.xml",
    ],
}
