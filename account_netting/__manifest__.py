# Copyright 2015 Pedro M. Baeza
# Copyright 2017 Vicent Cubells - Tecnativa <vicent.cubells@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Account netting",
    "version": "14.0.1.0.0",
    "summary": "Compensate AR/AP accounts from the same partner",
    "category": "Accounting & Finance",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "wizards/account_move_make_netting_view.xml",
    ],
    "installable": True,
}
