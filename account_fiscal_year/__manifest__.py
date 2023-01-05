# Copyright 2016 Camptocamp SA
# Copyright 2018 Lorenzo Battistini <https://github.com/eLBati>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account Fiscal Year",
    "summary": "Create a menu for Account Fiscal Year",
    "version": "12.0.1.0.1",
    "development_status": "Production/Stable",
    "category": "Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Agile Business Group, Camptocamp SA, "
              "Odoo Community Association (OCA)",
    "maintainers": ["eLBati"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account",
        "date_range",
    ],
    "data": [
        "data/date_range_type.xml",
        "views/account_views.xml"
    ],
}
