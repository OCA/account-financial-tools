# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Account financial discount",
    "version": "13.0.1.0.0",
    "category": "Account",
    "website": "camptocamp.com",
    "author": "Camptocamp",
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "account",
        "account_reconcile_model_strict_match_amount",
    ],
    "data": [
        "views/assets.xml",
        "views/payment_term_form.xml",
        "views/account_move.xml",
        "views/account_payment.xml",
        "views/account_reconcile_model.xml",
        "views/res_config_settings.xml",
        "views/payment_receipt.xml"
    ],
    "qweb": [
        "static/src/xml/reconciliation_templates.xml",
    ],
}
