# -*- coding: utf-8 -*-
# © 2010 Zikzakmedia S.L. (http://www.zikzakmedia.com)
# © 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
# © 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# © 2015 Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
# © 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# © 2016 Jacques-Etienne Baudoux <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Detect changes and update the Account Chart from a template",
    "summary": "Wizard to update a company's account chart from a template",
    'version': "9.0.1.0.0",
    'author': "Zikzakmedia SL, "
              "Pexego, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "ACSONE A/V, "
              "Tecnativa, "
              "BCIM,"
              "Odoo Community Association (OCA)",
    'website': "http://odoo-community.org",
    'depends': ["account"],
    'category': "Accounting & Finance",
    'contributors': [
        'Joaquín Gutierrez',
        'Pedro M. Baeza',
        'invitu',
        'Stéphane Bidoul',
        'Jairo Llopis',
        'Jacques-Etienne Baudoux',
    ],
    'license': "AGPL-3",
    "data": [
        'wizard/wizard_chart_update_view.xml',
        'views/account_config_settings_view.xml',
    ],
    'installable': True,
}
