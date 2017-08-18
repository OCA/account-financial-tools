# -*- coding: utf-8 -*-
# Copyright 2015-2017 Pedro Manuel Baeza <pedro.baeza@tecnativa.com>
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2016 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Account Chart Update",
    "summary": "Update a company's Account Chart from a template",
    'version': "10.0.1.0.0",
    'author': "Tecnativa, "
              "BCIM, "
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/account-financial-tools",
    'depends': ["account"],
    'category': "Accounting & Finance",
    'contributors': [
        'Pedro M. Baeza',
        'Jairo Llopis',
        'Jacques-Etienne Baudoux',
    ],
    'license': "AGPL-3",
    "data": [
        'wizard/wizard_chart_update_view.xml',
        'views/account_config_settings_view.xml',
    ],
}
