# -*- coding: utf-8 -*-
##############################################################################
#
#  OpenERP - Account invoice currency
#  Copyright (C) 2004-2011 Zikzakmedia S.L. (http://zikzakmedia.com)
#                         Jordi Esteve <jesteve@zikzakmedia.com>
#  Copyright (c) 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
#  Copyright (c) 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': "Company currency in invoices",
    'version': "10.0.1.0.0",
    'author': "Zikzakmedia SL, Odoo Community Association (OCA), "
              "Joaquín Gutierrez, "
              "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Sébastien Namèche",
    'website': "http://www.zikzakmedia.com, "
               "http://www.gutierrezweb.es, "
               "http://www.serviciosbaeza.com",
    'category': "Accounting",
    'license': "AGPL-3",
    'depends': ["account"],
    'data': [
        "views/account_invoice.xml"
    ],
    'installable': True,
}
