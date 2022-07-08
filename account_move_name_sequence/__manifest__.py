# Copyright 2021 Akretion France (http://www.akretion.com/)
# Copyright 2022 Vauxoo (https://www.vauxoo.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# @author: Moisés López <moylop260@vauxoo.com>
# @author: Francisco Luna <fluna@vauxoo.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Move Number Sequence",
    "version": "14.0.1.3.0",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Generate journal entry number from sequence",
    "author": "Akretion,Vauxoo,Odoo Community Association (OCA)",
    "maintainers": ["alexis-via", "moylop260", "frahikLV"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_journal.xml",
        "views/account_move.xml",
        "security/ir.model.access.csv",
    ],
    "post_init_hook": "create_journal_sequences",
    "installable": True,
}
