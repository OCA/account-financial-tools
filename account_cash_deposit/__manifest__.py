# Copyright 2022 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Cash Deposit",
    "version": "14.0.1.0.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Manage cash deposits and cash orders",
    "author": "Akretion, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "wizards/account_cash_order_reception_view.xml",
        "data/sequence.xml",
        "data/cash_unit_eur.xml",
        "data/cash_unit_usd.xml",
        "data/cash_unit_chf.xml",
        "data/cash_unit_cad.xml",
        "views/account_cash_deposit.xml",
        "views/cash_unit.xml",
        "views/res_currency.xml",
        "report/report.xml",
        "report/report_cashdeposit.xml",
    ],
    "installable": True,
}
