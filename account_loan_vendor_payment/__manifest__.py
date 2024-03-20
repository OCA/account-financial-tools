{
    "name": "Account Loan Vendor Payment",
    "summary": """Loan for a vendor payment""",
    "author": "Nextev Srl, Ooops, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "AGPL-3",
    "category": "Account",
    "version": "14.0.1.0.0",
    "depends": [
        "account_loan",
    ],
    "data": [
        "wizard/account_payment_register_views.xml",
        "views/account_move.xml",
        "views/account_payment.xml",
    ],
    "installable": True,
    "application": False,
}
