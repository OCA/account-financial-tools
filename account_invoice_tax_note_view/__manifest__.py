# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': "Account invoice tax note view",
    'version': "12.0.1.0.0",
    "author": "Decodio Applications,Odoo Community Association (OCA)",
    "development_status": "Production/Stable",
    "summary": "Adding missing filed on view when OCA account_invoice_tax_note """
               "and account_group_menu are installed",
    'website': "https://github.com/OCA/account-financial_tools",
    'category': "Localization / Accounting",
    'license': "AGPL-3",
    'depends': [
        "account_invoice_tax_note",
        "account_group_menu"
    ],
    'data': [
        'views/account_tax_group.xml',
    ],
    'installable': True,
    'auto_install': True
}
