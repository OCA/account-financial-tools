# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

FINANCIAL_DEBT = [
    ('2receive', 'Account Receivable'),  # r
    ('2pay', 'Account Payable'),  # p
]
FINANCIAL_DEBT_2RECEIVE = '2receive'
FINANCIAL_DEBT_2PAY = '2pay'

FINANCIAL_IN_OUT = [
    ('receipt_item', 'Receipt Item'),  # rr
    ('payment_item', 'Payment Item'),  # pp
    ('money_in', 'Money In'),
    ('money_out', 'Money Out'),
]
FINANCIAL_RECEIPT = 'receipt_item'
FINANCIAL_PAYMENT = 'payment_item'
FINANCIAL_MONEY_IN = 'money_in'
FINANCIAL_MONEY_OUT = 'money_out'

FINANCIAL_INCOMING_MOVE = [
    FINANCIAL_RECEIPT,
    FINANCIAL_MONEY_IN,
]
FINANCIAL_OUTGOING_MOVE = [
    FINANCIAL_PAYMENT,
    FINANCIAL_MONEY_OUT,
]

FINANCIAL_TYPE = FINANCIAL_DEBT + FINANCIAL_IN_OUT

FINANCIAL_STATE = [
    ('draft', 'Draft'),
    ('open', 'Open'),
    ('paid', 'Paid'),
    ('cancel', 'Cancel'),
]

FINANCIAL_SEQUENCE = {
    '2receive': 'financial.move.receivable',
    'receipt_item': 'financial.move.receipt',
    '2pay': 'financial.move.payable',
    'payment_item': 'financial.move.payment',
}


FINANCIAL_MOVE_FIELD = (
    ('amount_document', 'Document amount'),
    ('amount_interest', 'Interest amount'),
    ('amount_penalty', 'Penalty amount'),
    ('amount_other_credits', 'Other credits amount'),
    ('amount_discount', 'Discount amount'),
    ('amount_other_debits', 'Other debits amount'),
    ('amount_bank_fees', 'Bank fees amount'),
    ('amount_refund', 'Refund amount'),
    ('amount_cancel', 'Cancelled amount'),
    ('amount_total', 'Total amount'),
    ('amount_paid', 'Paid amount'),
    ('amount_residual', 'Residual amount'),
)
