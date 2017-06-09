# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Financial',
    'summary': """
        Financial""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'l10n_br_resource',
        'copy_views',
        'account',
        'mail',
    ],
    'data': [
        'data/ir_sequence_data.xml',
        # 'data/financial_move_data.xml',
        'views/financial_menu.xml',
        'views/financial_move_payment_base_view.xml',
        'views/financial_move_debt_base_view.xml',
        'views/financial_move_debt_2receive_view.xml',
        'views/financial_move_debt_2pay_view.xml',
        # 'views/payment_mode.xml',
        'views/inherited_account_account_type_view.xml',
        'views/inherited_account_account_view.xml',
        'views/financial_document_type_view.xml',
        'views/financial_account_move_template_view.xml',
        'views/inherited_res_partner_bank_view.xml',
        'views/inherited_account_journal_view.xml',

        # 'wizards/financial_cancel.xml',
        # 'wizards/financial_edit.xml',
        # 'wizards/financial_create.xml',
        # 'wizards/financial_pay_receive.xml',
        'wizards/financial_cashflow.xml',

        # 'report/financial_cashflow.xml',
        # 'report/financial_statement_report.xml',
        # 'report/report_financial.xml',
        'report/financial_cashflow_report.xml',

        # 'security/inherited_account_account_type_security.xml',
        'security/inherited_res_partner_bank_security.xml',
        # 'security/financial_move_security.xml',
    ],
    'demo': [
        'demo/financial_move.xml',
        # 'demo/financial_demo.yml'
    ],
}
