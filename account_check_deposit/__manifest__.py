# Copyright 2012-2021 Akretion France (http://www.akretion.com/)
# @author: Benoît GUILLOT <benoit.guillot@akretion.com>
# @author: Chafique DELLI <chafique.delli@akretion.com>
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# Copyright 2018-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Check Deposit",
    "version": "15.0.1.0.1",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Manage deposit of checks to the bank",
    "author": "Akretion, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "development_status": "Mature",
    "data": [
        "security/ir.model.access.csv",
        "security/check_deposit_security.xml",
        "data/sequence.xml",
        "views/account_check_deposit_view.xml",
        "views/account_move_line_view.xml",
        "report/report.xml",
        "report/report_checkdeposit.xml",
    ],
    "installable": True,
}
