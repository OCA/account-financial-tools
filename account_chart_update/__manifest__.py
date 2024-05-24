# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2016 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2016 Sylvain Van Hoof <sylvain@okia.be>
# Copyright 2015-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Detect changes and update the Account Chart from a template",
    "summary": "Wizard to update a company's account chart from a template",
    "version": "13.0.1.0.5",
    "author": "Tecnativa, BCIM, Okia, Odoo Community Association (OCA)",
    "website": "http://github.com/OCA/account-financial-tools",
    "depends": ["account"],
    "category": "Accounting",
    "license": "AGPL-3",
    "data": [
        "wizard/wizard_chart_update_view.xml",
        "views/account_config_settings_view.xml",
    ],
    "installable": True,
}
