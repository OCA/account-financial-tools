# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "User Journal Preferences",
    "summary": "Prioritize journals according to each user's preferences",
    "version": "18.0.1.0.1",
    "development_status": "Beta",
    "category": "Accounting/Accounting",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["matthieusaison"],
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/account_journal_user_preferred_security.xml",
        "views/res_users_views.xml",
    ],
    "installable": True,
}
