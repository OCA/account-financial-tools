# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "EBITDA Report (MIS Builder)",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/Reporting",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "summary": "Professional EBITDA report with M&A normalizations.",
    "depends": ["account", "mis_builder"],
    "data": [
        "data/account_tag_data.xml",
        "data/mis_report_ebitda.xml",
    ],
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}
