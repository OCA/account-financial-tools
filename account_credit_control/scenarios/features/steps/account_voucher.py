from support import *
import datetime

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
    if ctx.line.voucher_id:
        model('account.voucher').write([ctx.line.voucher_id.id],
                                       {'amount': float(amount)})
    ctx.line.write({'amount': float(amount)})

@step('My invoice "{inv_name}" is in state "{state}" reconciled with a residual amount of "{amount:f}"')
def impl(ctx, inv_name, state, amount):
    invoice = model('account.invoice').get([('name', '=', inv_name)])
    assert_almost_equal(invoice.residual, amount)
    assert_equal(invoice.state, state)


@step('I should have following journal entries in voucher')
@step('I should have the following journal entries in voucher')
def impl(ctx):
    rows = []
    for row in ctx.table:
        cells = {}
        for key, value in row.items():
            if value:
               cells[key] = value
        rows.append(cells)
    bank_statement = ctx.found_item
    assert_equal(len(bank_statement.move_line_ids), len(rows))
    errors = []
    for row in rows:
        account = model('account.account').get([('name', '=', row['account'])])
        if 'curr.' in row:
            currency_id = mode('res.currency').get([('name', '=', row['curr.'])]).id
        else:
            currency_id = False
    pname = datetime.datetime.now().strftime(row['period'])
    period = model('account.period').get([('name', '=', pname)])
    domain = [('account_id', '=', account.id),
              ('period_id', '=', period.id),
              ('date', '=', datetime.datetime.now().strftime(row['date'])),
              ('credit', '=', row.get('credit', 0.)),
              ('debit', '=', row.get('debit', 0.)),
              ('amount_currency', '=', row.get('curr.amt', 0.)),
              ('currency_id', '=', currency_id),
              ('id', 'in', [line.id for line in bank_statment.move_line_ids]),
              ]
    if row.get('reconcile'):
        domain.append(('reconcile_id', '!=', False))
    else:
        domain.append(('reconcile_id', '=', False))
    if row.get('partial'):
        domain.append(('reconcile_partial_id', '!=', False))
    else:
        domain.append(('reconcile_partial_id', '=', False))
    line = model('account.move.line').get(domain)

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
