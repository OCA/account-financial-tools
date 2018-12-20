# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Account Tax Note",
    "summary": "Allows to display a footer note related to taxes in invoices",
    'version': "11.0.1.0.0",
    'author': "Eficent, "
              "Odoo Community Association (OCA)",
    'website': "http://github.com/OCA/account-financial-tools",
    'depends': ["account"],
    'category': "Accounting",
    'license': "AGPL-3",
    "data": [
        'views/account_tax_views.xml',
        "views/report_invoice.xml",
    ],
    'installable': True,
}
