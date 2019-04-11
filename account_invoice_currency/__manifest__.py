# © 2004-2011 Pexego Sistemas Informáticos. (http://pexego.es)
# © 2004-2011 Zikzakmedia S.L. (http://zikzakmedia.com)
#             Jordi Esteve <jesteve@zikzakmedia.com>
# © 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Antonio Espinosa - <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': "Company currency in invoices",
    'version': "12.0.1.0.0",
    'author': "Zikzakmedia SL, "
              "Joaquín Gutierrez, "
              "Tecnativa, "
              "Softdil S.L, "
              "Odoo Community Association (OCA) ",
    'website': "https://github.com/OCA/account-financial-tools",
    'category': "Accounting",
    'license': "AGPL-3",
    'depends': ["account"],
    'data': [
        "views/account_invoice.xml"
    ],
    'installable': True,
}
