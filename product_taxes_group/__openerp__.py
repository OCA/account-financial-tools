# -*- encoding: utf-8 -*-
##############################################################################
#
#    Product - Taxes Group module for Odoo
#    Copyright (C) 2014 -Today GRAP (http://www.grap.coop)
#    @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Product - Taxes Group',
    'summary': 'Simplify taxes management for products with Taxes Group',
    'version': '0.2',
    'category': 'product',
    'description': """
Simplify taxes management for products with Taxes Group
=======================================================

Functionality:
--------------
    * Add a new light concept 'tax_group' to associate possible supplier
      and sale taxes;
    * Make more usable taxes selection in product view. The user has now the
      possibility to select a tax group, instead of select manually all
      the taxes;
    * Prevent users to select incompatible purchase and supplier taxes.
      French Exemple: A product can not be configured with:
        * Supplier Taxes: 5.5 %;
        * Sale Taxes: 20%;
    * Provides the possibility to the account manager to change incorrect
      parameters massively;

Technical Information:
----------------------
    * Install this module will create 'tax_group' for each existing
      combination.
    * In the same way, import products will create tax_group if combination
      doesn't exist and will fail if right access is not sufficient. Make sure
      that the user who realize the import is SUPERUSER_ID or is member of
      account.group_account_manager;
      An alternative solution is to provide tax_group_id during the import,
      instead of providing taxes_id and purchase_taxes_id fields;

Copyright, Authors and Licence:
-------------------------------
    * Copyright: 2014, GRAP: Groupement Régional Alimentaire de Proximité;
    * Author:
        * Sylvain LE GAL (https://twitter.com/legalsylvain);""",
    'author': 'GRAP',
    'website': 'http://www.grap.coop',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'stock',
    ],
    'data': [
        'security/ir_model_access.yml',
        'view/action.xml',
        'view/view.xml',
        'view/menu.xml',
    ],
    'demo': [
        'demo/account_tax.yml',
        'demo/tax_group.yml',
        'demo/product_product.yml',
    ],
}
