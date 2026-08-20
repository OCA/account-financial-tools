{
    "name": "Manual validation of European VAT number",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Accounting/Accounting",
    "website": "https://github.com/OCA/account-financial-tools",
    "author": "Le Filament, Odoo S.A., OCA France, Odoo Community Association (OCA)",
    "maintainers": ["remi-filament"],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "preloadable": True,
    "depends": [
        "base_vat",
    ],
    "data": [
        "data/ir_cron_data.xml",
        "views/res_config_settings_views.xml",
        "views/res_partner_view.xml",
    ],
}
