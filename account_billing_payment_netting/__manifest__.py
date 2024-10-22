# Copyright 2023 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

{
    "name": "Account Billing Payment Netting",
    "version": "16.0.1.0.0",
    "summary": "Net Payment on AR/AP billing from the same partner",
    "category": "Accounting & Finance",
    "author": "Ecosoft, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account_billing", "account_payment_netting"],
    "data": [
        "views/account_billing_views.xml",
    ],
    "installable": True,
    "development_status": "Alpha",
    "maintainers": ["Saran440"],
}
