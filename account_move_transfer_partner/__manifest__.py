# Copyright 2022 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Transfer Partner",
    "summary": "Automation to translate amount due from many partners to one partner",
    "version": "14.0.1.0.0",
    "author": "ForgeFlow S.L., " "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["account"],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "wizard/wizard_account_move_transfer_partner_view.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["ChrisOForgeFlow"],
}
