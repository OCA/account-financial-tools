# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#           (www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Line Purchase Info",
    "summary": "Introduces the purchase order line to the journal items",
    "version": "11.0.1.1.0",
    "author": "Eficent, "
              "Odoo Community Association (OCA)",
    "website": "http://www.github.com/OCA/account-financial-tools",
    "category": "Generic",
    "depends": ["purchase"],
    "license": "AGPL-3",
    "data": [
        "security/account_security.xml",
        "views/account_move_view.xml",
    ],
    'installable': True,
}
