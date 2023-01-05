# Copyright 2020 Sergio Zanchetta (Associazione PNLUG - Gruppo Odoo)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Receipt Printing',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'summary': 'Enable printing in sale and purchase receipts',
    'author': 'Pordenone Linux User Group (PNLUG), Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/account-financial-tools',
    'license': 'AGPL-3',
    'depends': [
        'account_voucher'],
    'data': ['views/report_receipt.xml',
             'views/account_report.xml'],
    'installable': True,
}
