# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

FINANCIAL_MOVE = [
    ('2receive', 'Account Receivable'),  # r
    ('2pay', 'Account Payable'),  # p
]

FINANCIAL_IN_OUT = [
    ('receipt_item', 'Receipt Item'),  # rr
    ('payment_item', 'Payment Item'),  # pp
    ('money_in', 'Money In'),
    ('money_out', 'Money Out'),
]

FINANCIAL_TRANSFER = [
    ('transfer', 'Transfer')
]

FINANCIAL_TYPE = FINANCIAL_MOVE + FINANCIAL_IN_OUT + FINANCIAL_TRANSFER

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
