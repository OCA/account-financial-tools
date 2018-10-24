# Copyright 2018 FIEF Management SA (www.fief.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Reclassify",
    "summary": "Wizard that can help reclassify multiple move lines at once",
    "version": "11.0.1.0.0",
    "author": "FIEF Management SA, "
              "Odoo Community Association (OCA)",
    "website": "http://www.github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["account"],
    "license": "AGPL-3",
    "data": [
        'views/account_move_line_view.xml',
        'wizards/reclassify_account_move_line_view.xml',
    ],
    'installable': True,
}
