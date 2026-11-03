# Copyright 2026 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
{
    "name": "Account Move From EPD",
    "summary": "Materialize Early Payment Discount as a Journal Entry",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["grindtildeath"],
    "license": "AGPL-3",
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizard/account_move_from_epd_generator_views.xml",
        "views/account_move_views.xml",
    ],
}
