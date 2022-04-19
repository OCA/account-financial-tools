# Copyright 2016 Camptocamp SA
# Copyright 2018 Lorenzo Battistini <https://github.com/eLBati>
# Copyright 2020 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Fiscal Year",
    "summary": "Create Account Fiscal Year",
    "version": "14.0.1.2.0",
    "development_status": "Production/Stable",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools"
    "14.0/account_fiscal_year",
    "author": "Agile Business Group, Camptocamp SA, "
    "Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "AGPL-3",
    "depends": ["account", "date_range"],
    "data": [
        "security/ir.model.access.csv",
        "data/date_range_type.xml",
        "security/account_fiscal_year_rule.xml",
        "views/account_fiscal_year_views.xml",
    ],
}
