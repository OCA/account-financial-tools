# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

FINANCIAL_DEBT = [
    ('2receive', 'Receivable'),
    ('2pay', 'Payable'),
]
FINANCIAL_DEBT_2RECEIVE = '2receive'
FINANCIAL_DEBT_2PAY = '2pay'

FINANCIAL_IN_OUT = [
    ('receipt_item', 'Receipt Item'),
    ('payment_item', 'Payment Item'),
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
FINANCIAL_TYPE_DICT = dict(FINANCIAL_TYPE)

FINANCIAL_TYPE_CODE = {
    FINANCIAL_DEBT_2RECEIVE: 'FR',
    FINANCIAL_DEBT_2PAY: 'FP',
    FINANCIAL_RECEIPT: 'RR',
    FINANCIAL_PAYMENT: 'PP',
    FINANCIAL_MONEY_IN: 'MI',
    FINANCIAL_MONEY_OUT: 'MO',
}

FINANCIAL_STATE = [
    ('draft', 'Draft'),
    ('open', 'Open'),
    ('paid', 'Paid'),
    ('cancelled', 'Cancelled'),
]
FINANCIAL_STATE_DRAFT = 'draft'
FINANCIAL_STATE_OPEN = 'open'
FINANCIAL_STATE_PAID = 'paid'
FINANCIAL_STATE_CANCELLED = 'cancelled'

FINANCIAL_DEBT_STATUS = [
    ('due', 'Due'),
    ('due_today', 'Due today'),
    ('overdue', 'Overdue'),
    ('paid', 'Paid'),
    ('paid_partially', 'Partially paid'),
    ('cancelled', 'Cancelled'),
    ('cancelled_partially', 'Partially cancelled'),
]

FINANCIAL_DEBT_STATUS_DUE = 'due'
FINANCIAL_DEBT_STATUS_DUE_TODAY = 'due_today'
FINANCIAL_DEBT_STATUS_OVERDUE = 'overdue'
FINANCIAL_DEBT_STATUS_PAID = 'paid'
FINANCIAL_DEBT_STATUS_PAID_PARTIALLY = 'paid_partially'
FINANCIAL_DEBT_STATUS_CANCELLED = 'cancelled'
FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY = 'cancelled_partially'

FINANCIAL_DEBT_STATUS_CONSIDERS_OPEN = [
    FINANCIAL_DEBT_STATUS_DUE,
    FINANCIAL_DEBT_STATUS_DUE_TODAY,
    FINANCIAL_DEBT_STATUS_OVERDUE,
    FINANCIAL_DEBT_STATUS_PAID_PARTIALLY,
]

FINANCIAL_DEBT_STATUS_CONSIDERS_PAID = [
    FINANCIAL_DEBT_STATUS_PAID,
    FINANCIAL_DEBT_STATUS_PAID_PARTIALLY,
    FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY,
]

FINANCIAL_DEBT_STATUS_CONSIDERS_CANCELLED = [
    FINANCIAL_DEBT_STATUS_CANCELLED,
    FINANCIAL_DEBT_STATUS_CANCELLED_PARTIALLY,
]

FINANCIAL_DEBT_CONCISE_STATUS = [
    ('open', 'Open'),
    ('paid', 'Paid'),
    ('cancelled', 'Cancelled'),
]

FINANCIAL_DEBT_CONCISE_STATUS_OPEN = 'open'
FINANCIAL_DEBT_CONCISE_STATUS_PAID = 'paid'
FINANCIAL_DEBT_CONCISE_STATUS_CANCELLED = 'cancelled'

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

FINANCIAL_INSTALLMENT_STATE = (
    ('draft', 'Draft'),
    ('confirmed', 'Confirmed'),
)
FINANCIAL_INSTALLMENT_STATE_DRAFT = 'draft'
FINANCIAL_INSTALLMENT_STATE_CONFIRMED = 'confirmed'
