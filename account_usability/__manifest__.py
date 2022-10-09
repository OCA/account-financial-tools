# Copyright (C) 2019 - Today: GRAP (http://www.grap.coop)
# @author: Sylvain LE GAL (https://twitter.com/legalsylvain)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    "name": "Account - Missing Menus & Saxon Accounting",
    "version": "16.0.1.0.1",
    "category": "Accounting",
    "license": "AGPL-3",
    "summary": "Adds missing menu entries for Account module and"
    " adds the option to enable Saxon Accounting",
    "author": "GRAP, Akretion, Odoo Community Association (OCA)",
    "maintainers": ["legalsylvain"],
    "website": "https://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "data": [
        "data/ir_module_category.xml",
        "security/res_groups.xml",
        "views/menu.xml",
        "views/res_config_settings_views.xml",
        "views/view_account_bank_statement.xml",
        "views/view_account_group.xml",
        "views/view_account_tag.xml",
        "views/view_account_chart_template.xml",
        "views/view_account_account_template.xml",
        "views/view_account_tax_template.xml",
        "views/view_account_fiscal_position_template.xml",
    ],
    "demo": ["demo/res_groups.xml"],
    "installable": True,
}
