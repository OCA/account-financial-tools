# Copyright 2026 - TODAY, Cristiano Mafra Junior <cristiano.mafra@escodoo.com.br>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Truncation Base",
    "summary": """
        Shared infrastructure to truncate (instead of round) monetary
        amounts, based on named Decimal Accuracy precisions""",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), Escodoo",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "base",
    ],
    "data": [
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
    ],
    "maintainers": ["CristianoMafraJunior"],
    "application": False,
    "installable": True,
}
