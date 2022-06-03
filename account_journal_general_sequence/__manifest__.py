# Copyright 2022 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "General sequence in account journals",
    "summary": "Add configurable sequence to account moves, per journal",
    "version": "14.0.1.0.1",
    "category": "Accounting/Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Moduon, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "external_dependencies": {"python": ["freezegun"]},
    "maintainers": ["yajo"],
    "depends": [
        "account",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_journal.xml",
        "views/account_move_line.xml",
        "views/account_move.xml",
        "wizards/account_move_renumber_wizard_views.xml",
    ],
}
