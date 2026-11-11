# Copyright 2026 Heliconia Solutions Pvt. Ltd.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Account Move Intercompany",
    "summary": "Allow to transfer amount to other companies",
    "version": "18.0.1.0.0",
    "category": "Accounting & Finance",
    "author": "Heliconia Solutions Pvt. Ltd., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": ["base", "account"],
    "data": [
        "security/ir_rule.xml",
        "security/ir.model.access.csv",
        "views/account_move_view.xml",
        "data/mail_template_data.xml",
        "views/intercompany_transaction_config_view.xml",
        "views/res_company_view.xml",
        "views/menuitems.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
    "maintainers": ["Bhavesh Heliconia"],
    "development_status": "Beta",
}
