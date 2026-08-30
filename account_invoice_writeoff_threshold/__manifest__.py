{
    "name": "Account Invoice Write-off Threshold",
    "summary": "Automatically write off invoice residual balances below a threshold",
    "version": "17.0.1.0.0",
    "author": "Jarsa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/account-financial-tools",
    "license": "LGPL-3",
    "category": "Accounting/Accounting",
    "depends": ["account"],
    "data": [
        "security/account_writeoff_threshold_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence.xml",
        "views/res_config_settings_views.xml",
        "views/account_writeoff_log_views.xml",
        "views/account_writeoff_threshold_wizard_views.xml",
    ],
}
