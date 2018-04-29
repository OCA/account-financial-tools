# © 2008-2016 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Currency Rate Update",
    "version": "11.0.0.0.0",
    "author": "Camptocamp,Odoo Community Association (OCA)",
    "website": "http://camptocamp.com",
    "license": "AGPL-3",
    "category": "Financial Management/Configuration",
    "depends": [
        "base",
        "mail",
        "account",  # Added to ensure account security groups are present
    ],
    "data": [
        "data/cron.xml",
        "views/currency_rate_update.xml",
        "views/res_config_settings.xml",
        "security/rule.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True
}
