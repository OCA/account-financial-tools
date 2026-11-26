# Copyright 2026 Saad Elbahi
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Account Move Review",
    "summary": "Entry review workflow, draft reset control, and document types",
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Saad Elbahi, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "development_status": "Beta",
    "maintainers": ["saadhp"],
    "depends": [
        "account",
        "mail",
    ],
    "data": [
        "security/account_move_review_security.xml",
        "security/ir.model.access.csv",
        "wizards/account_move_review_wizard_views.xml",
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
