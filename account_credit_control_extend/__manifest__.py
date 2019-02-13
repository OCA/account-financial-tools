# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# Copyright 2018 Access Bookings Ltd (https://accessbookings.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{'name': 'Account Credit Control add credit limit',
 'version': '11.0.1.0.1',
 'author': "Rosen Vladimirov,"
           "Camptocamp,"
           "Odoo Community Association (OCA),"
           "Okia,"
           "Access Bookings,"
           "Tecnativa",
 'category': 'Finance',
 'depends': [
     'base',
     'account',
     'sale',
     'mail',
     'account_credit_control',
     'website_sale',
 ],
 'website': 'https://github.com/OCA/account-financial-tools',
 'data': [
     # Views
     "views/account_invoice.xml",
     "views/res_partner.xml",
     "views/sale_views.xml",
     "views/templates.xml",
 ],
 'installable': True,
 'license': 'AGPL-3',
 'application': True
 }
