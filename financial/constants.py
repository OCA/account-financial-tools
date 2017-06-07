# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

FINANCIAL_DEBT = [
    ('2receive', 'Account Receivable'),  # r
    ('2pay', 'Account Payable'),  # p
]
FINANCIAL_DEBT_2RECEIVE = '2receive'
FINANCIAL_DEBT_2PAY = '2PAY'

FINANCIAL_IN_OUT = [
    ('receipt_item', 'Receipt Item'),  # rr
    ('payment_item', 'Payment Item'),  # pp
    ('money_in', 'Money In'),
    ('money_out', 'Money Out'),
]

FINANCIAL_TRANSFER = [
    ('transfer', 'Transfer')
]

FINANCIAL_TYPE = FINANCIAL_DEBT + FINANCIAL_IN_OUT + FINANCIAL_TRANSFER

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
