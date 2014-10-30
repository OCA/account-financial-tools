# -*- coding: utf-8 -*-
# flake8: noqa
from support import model, assert_equal, assert_almost_equal
import datetime


@step('I pay the full amount on the invoice "{inv_name}"')
def impl(ctx, inv_name):
    Invoice = model('account.invoice')
    invoice = Invoice.get([('name', '=', inv_name)])
    assert invoice
    ctx.execute_steps("""
       When I pay %f on the invoice "%s"
    """ % (invoice.residual, inv_name))


@step('I pay {amount:f} on the invoice "{inv_name}"')
def impl(ctx, amount, inv_name):
    Partner = model('res.partner')
    Invoice = model('account.invoice')
    Voucher = model('account.voucher')
    VoucherLine = model('account.voucher.line')
    Journal = model('account.journal')
    invoice = Invoice.get([('name', '=', inv_name)])
    assert invoice
    journal = Journal.get('scen.eur_journal')
    values = {
        'partner_id': invoice.partner_id.commercial_partner_id.id,
        'reference': invoice.name,
        'amount': amount,
        'date': invoice.date_invoice,
        'currency_id': invoice.currency_id.id,
        'company_id': invoice.company_id.id,
        'journal_id': journal.id,
    }

    if invoice.type in ('out_invoice','out_refund'):
        values['type'] = 'receipt'
    else:
        values['type'] = 'payment'

    onchange = Voucher.onchange_partner_id([], values['partner_id'],
                                           values['journal_id'],
                                           values['amount'],
                                           values['currency_id'],
                                           values['type'],
                                           values['date'])
    values.update(onchange['value'])

    onchange = Voucher.onchange_date([], values['date'],
                                     values['currency_id'],
                                     False,
                                     values['amount'],
                                     values['company_id'])
    values.update(onchange['value'])

    onchange = Voucher.onchange_amount([], values['amount'],
                                       False,
                                       values['partner_id'],
                                       values['journal_id'],
                                       values['currency_id'],
                                       values['type'],
                                       values['date'],
                                       False,
                                       values['company_id'])
    values.update(onchange['value'])
    values['line_cr_ids'] = False

    voucher = Voucher.create(values)

    vals = voucher.recompute_voucher_lines(voucher.partner_id.id,
                                           voucher.journal_id.id,
                                           voucher.amount,
                                           voucher.currency_id.id,
                                           voucher.type,
                                           voucher.date)
    for line in vals['value']['line_cr_ids']:
        line['voucher_id'] = voucher.id
        VoucherLine.create(line)

    for line in vals['value']['line_dr_ids']:
        line['voucher_id'] = voucher.id
        VoucherLine.create(line)

    voucher.button_proforma_voucher()
    # Workaround to force recomputation of the residual.
    # Must be removed once this bug is fixed:
    # https://github.com/odoo/odoo/issues/3395
    invoice.write({'currency_id': invoice.currency_id.id})


@step('My invoice "{inv_name}" is in state "{state}" reconciled with a residual amount of "{amount:f}"')
def impl(ctx, inv_name, state, amount):
    invoice = model('account.invoice').get([('name', '=', inv_name)])
    assert_almost_equal(invoice.residual, amount)
    assert_equal(invoice.state, state)
