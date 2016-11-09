# -*- coding: utf-8 -*-
# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2004-2011 Zikzakmedia S.L. (http://zikzakmedia.com)
#             Jordi Esteve <jesteve@zikzakmedia.com>
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Company currency in invoices",
    'version': "9.0.1.0.0",
    'author': "Zikzakmedia SL, "
              "Joaquín Gutierrez, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Tecnativa, "
              "Odoo Community Association (OCA) ",
    'website': "https://odoo-community.org/",
    'category': "Localisation / Accounting",
    'license': "AGPL-3",
    'depends': ["account"],
    'data': [
        "views/account_invoice_view.xml"
    ],
    'installable': True,
}
