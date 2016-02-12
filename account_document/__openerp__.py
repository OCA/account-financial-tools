# -*- coding: utf-8 -*-
{
    "name": "Account Documents Management",
    "version": "0.0.0.0.0",
    "author": "Moldeo Interactive,ADHOC SA",
    "license": "AGPL-3",
    "category": "Financial Management/Configuration",
    "depends": [
        "account",
    ],
    "data": [
        'view/account_journal_view.xml',
        'view/account_move_line_view.xml',
        'view/account_move_view.xml',
        'view/account_document_type_view.xml',
        'view/account_document_letter_view.xml',
        'view/account_vat_responsability_view.xml',
        'view/account_invoice_view.xml',
        'view/res_company_view.xml',
        'view/res_partner_view.xml',
        'view/report_invoice.xml',
    ],
    "demo": [
        'demo/account_document_letter_demo.xml',
        'demo/account.document.type.csv',
    ],
    'installable': True,
}
