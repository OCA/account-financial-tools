# Copyright 2020 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Fiscal Position Allowed Journal",
    "summary": """
        Allow defining allowed journals on fiscal positions.
        Related invoices can only use one of the allowed journals on the
        fiscal position.""",
    "version": "13.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting/Accounting",
    "license": "AGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": ["ThomasBinsfeld"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": ["views/account_fiscal_position.xml"],
    "demo": [],
}
