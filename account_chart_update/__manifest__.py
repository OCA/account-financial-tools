# -*- coding: utf-8 -*-
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# Copyright 2016 Jacques-Etienne Baudoux <je@bcim.be>
# Copyright 2016 Sylvain Van Hoof <sylvain@okia.be>
# Copyright 2015-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Detect changes and update the Account Chart from a template",
    "summary": "Wizard to update a company's account chart from a template",
    'version': "10.0.2.0.1",
    'author': "Tecnativa, "
              "BCIM, "
              "Okia, "
              "Odoo Community Association (OCA)",
    'website': "http://odoo-community.org",
    'depends': ["account"],
    'development_status': 'Mature',
    'category': "Accounting",
    'license': "AGPL-3",
    "data": [
        'wizard/wizard_chart_update_view.xml',
        'views/account_config_settings_view.xml',
    ],
}
