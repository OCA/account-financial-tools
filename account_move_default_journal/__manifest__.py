# Copyright 2021-2023 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Default Journal",
    "version": "14.0.1.0.0",
    "author": "Therp BV,Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "category": "Accounting & Finance",
    "summary": "Configure a default journal for new account moves",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account",
    ],
    "data": ["views/account_config_settings.xml", "views/res_company_views.xml"],
}
