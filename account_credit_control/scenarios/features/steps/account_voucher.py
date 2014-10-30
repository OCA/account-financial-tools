# -*- coding: utf-8 -*-
# flake8: noqa
from support import *
import datetime

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

@step('I import invoice "{inv_name}" using import invoice button')
def impl(ctx, inv_name):
    invoice = model('account.invoice').get([('name', '=', inv_name)])
    assert invoice
    bank_statement = ctx.found_item
    for line in bank_statement.line_ids:
        line.unlink()
    lines = model('account.move.line').browse([('move_id', '=', invoice.move_id.id),
                                               ('account_id', '=', invoice.account_id.id)])

    wizard = model('account.statement.from.invoice.lines').create({'line_ids': lines})
    wizard.populate_statement({'statement_id': bank_statement.id})

@given(u'I should have a "account.bank.statement.line" with name: "{name}" and amount: "{amount}"')
def impl(ctx, name, amount):
    assert ctx.found_item
    line =  model('account.bank.statement.line').get([('name', '=', name),
                                                      ('amount', '=', amount),
                                                      ('statement_id', '=', ctx.found_item.id)])
    assert line
    ctx.line = line

@given(u'I set the voucher paid amount to "{amount}"')
def impl(ctx, amount):
    assert ctx.line
    voucher = model('account.voucher').get(ctx.line.voucher_id.id)
    assert voucher

    vals = voucher.onchange_amount(float(amount),
                                   voucher.payment_rate,
                                   voucher.partner_id.id,
                                   voucher.journal_id.id if voucher.journal_id else False,
                                   voucher.currency_id.id if voucher.currency_id else False,
                                   voucher.type,
                                   voucher.date,
                                   voucher.payment_rate,
                                   voucher.company_id.id if voucher.company_id else false)
    vals = vals['value']
    vals.update({'amount': ctx.line.voucher_id.amount})
    voucher_line_ids = []
    voucher_line_dr_ids = []
    v_l_obj = model('account.voucher.line')
    for v_line_vals in vals.get('line_cr_ids', []) or []:
        v_line_vals['voucher_id'] = voucher.id
        voucher_line_ids.append(v_l_obj.create(v_line_vals).id)
    vals['line_cr_ids'] = voucher_line_ids

    for v_line_vals in vals.get('line_dr_ids', []) or []:
        v_line_vals['voucher_id'] = voucher.id
        voucher_line_dr_ids.append(v_l_obj.create(v_line_vals).id)
    vals['line_dr_ids'] = voucher_line_ids

    voucher.write(vals)
    ctx.vals = vals
    ctx.voucher = voucher

@given(u'I save the voucher')
def impl(ctx):
    assert True

@given(u'I modify the line amount to "{amount}"')
@then(u'I modify the line amount to "{amount}"')
def impl(ctx, amount):
    assert ctx.line
    # we have to change voucher amount before chaning statement line amount
    # if ctx.line.voucher_id:
    #     model('account.voucher').write([ctx.line.voucher_id.id],
    #                                    {'amount': float(amount)})
    ctx.line.write({'amount': float(amount)})

@step('My invoice "{inv_name}" is in state "{state}" reconciled with a residual amount of "{amount:f}"')
def impl(ctx, inv_name, state, amount):
    invoice = model('account.invoice').get([('name', '=', inv_name)])
    assert_almost_equal(invoice.residual, amount)
    assert_equal(invoice.state, state)

@step('I modify the bank statement line amount to {amount:f}')
def impl(ctx, amount):
    line = ctx.found_item.voucher_id.line_cr_ids[0]
    #ctx.voucher = model('account.voucher').get(ctx.found_item.voucher_id.id)
    ctx.found_item.on_change('onchange_amount', 'amount', (), amount)

@then(u'I set bank statement end-balance')
@given(u'I set bank statement end-balance')
def impl(ctx):
    assert ctx.found_item, "No statement found"
    ctx.found_item.write({'balance_end_real': ctx.found_item.balance_end})
    assert ctx.found_item.balance_end == ctx.found_item.balance_end_real

@when(u'I confirm bank statement')
def impl(ctx):
    assert ctx.found_item
    assert_equal(ctx.found_item._model._name, 'account.bank.statement')
    ctx.found_item.button_confirm_bank()
