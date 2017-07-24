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
        'base',
        'l10n_br_resource',  # FIXME: Implementar esta funcionalidade no core
        'mail',
        'report_xlsx',
        # 'account_payment_mode' # FIXME: Modulo da OCA/bank-payment in v10
        # Estamos temporariamente dependendo deste módulo pois na v8 o model
        # payment.mode esta no core.
        'account_payment',
        #
        # Em um futuro distante não deveremos mais depender de account, pois os
        # models:
        #   - account.payment.term
        #   - account.payment.mode
        # Estarão em um módulo separado
        #
        # TODO: Criar um PR no core separando models do módulo account
        #
        'account',
    ],
    'data': [
        'views/financial_menu.xml',

        'data/financial_document_type_data.xml',
        'data/interest_data.xml',
        # 'data/financial_move_data.xml',

        'wizards/financial_cancel.xml',
        # 'wizards/financial_edit.xml',
        # 'wizards/financial_pay_receive.xml',
        'wizards/report_xlsx_financial_cashflow_wizard_view.xml',
        'wizards/report_xlsx_financial_moves_states_wizard.xml',
        'views/financial_move_payment_one2many_base_view.xml',
        'views/financial_move_debt_base_view.xml',
        'views/financial_move_debt_2receive_view.xml',
        'views/financial_move_debt_2pay_view.xml',

        'views/financial_move_payment_base_view.xml',
        'views/financial_move_payment_receipt_item_view.xml',
        'views/financial_move_payment_payment_item_view.xml',

        'views/financial_installment_base_view.xml',
        'views/financial_installment_2receive_view.xml',
        'views/financial_installment_2pay_view.xml',

        'views/financial_document_type_view.xml',
        'views/financial_account_view.xml',
        'views/inherited_res_partner_bank_view.xml',

        # 'report/financial_cashflow.xml',
        # 'report/financial_statement_report.xml',
        # 'report/report_financial.xml',
        'reports/report_xlsx_financial_cashflow_data.xml',
        'reports/report_xlsx_financial_moves_states_data.xml',

        # 'security/inherited_res_partner_bank_security.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        'demo/financial_move.xml',
        'demo/financial.account.csv',
        'demo/financial_demo.yml'
    ],
    'test': [
        'test/financial_move_test.yml',
    ]
}
