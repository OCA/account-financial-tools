# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Landed Cost Info",
    "summary": "Introduces the landed cost adjustment lines to the journal items",
    "version": "14.0.1.0.0",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["stock_landed_costs"],
    "license": "AGPL-3",
    "data": ["views/account_move_view.xml"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
