# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Assets Unit of Activity",
    "summary": "Add a depreciation method based on the asset unit of activity",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_asset_management"],
    "author": "Akretion, Odoo Community Association (OCA)",
    "maintainers": ["florian-dacosta", "matthieusaison"],
    "website": "https://github.com/OCA/account-financial-tools",
    "category": "Accounting & Finance",
    "data": [
        "security/ir.model.access.csv",
        "views/account_asset_profile.xml",
        "views/account_asset.xml",
        "wizard/account_asset_unit_of_activity.xml",
    ],
}
