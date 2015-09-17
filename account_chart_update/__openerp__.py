# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 Zikzakmedia S.L. (http://www.zikzakmedia.com)
#    Copyright (c) 2010 Pexego Sistemas Informáticos S.L.(http://www.pexego.es)
#    Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    2013/09/08 - Joaquín Gutierrez: Adaptación a la versión
#
##############################################################################

{
    'name': "Detect changes and update the Account Chart from a template",
    'version': "8.0.1.2.0",
    'author': "Zikzakmedia SL, "
              "Pexego, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "ACSONE A/V, "
              "Odoo Community Association (OCA)",
    'website': "http://odoo-community.org",
    'depends': ["account"],
    'category': "Generic Modules/Accounting",
    'contributors': [
        'Joaquín Gutierrez',
        'Pedro M. Baeza',
        'invitu',
        'Stéphane Bidoul',
    ],
    'license': "AGPL-3",
    "demo": [],
    "data": [
        'wizard/wizard_chart_update_view.xml',
        'views/account_tax_code_view.xml',
    ],
    "active": False,
    'installable': True
}
