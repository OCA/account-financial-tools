import time
from behave import given, when
from support import model

@given(u'I configure the following accounts on the credit control policy with oid: "{policy_oid}"')
def impl(ctx, policy_oid):
    policy = model('credit.control.policy').get(policy_oid)
    assert policy, 'No policy % found' % policy_oid
    acc_obj = model('account.account')
    accounts = []
    for row in ctx.table:
        acc = acc_obj.get(['code = %s' % row['account code']])
        assert acc,  "Account with code %s not found" % row['account code']
        accounts.append(accounts)
    policy.write({'account_ids': accounts})


@when(u'I launch the credit run')
def impl(ctx):
    assert ctx.found_item
    # Must be a cleaner way to do it
    assert 'credit.control.run' == ctx.found_item._model._name
    ctx.found_item.generate_credit_lines()

@given(u'I clean all the credit lines')
def impl(ctx):
    model('credit.control.line').browse([]).unlink()

@then(u'my credit run should be in state "done"')
def impl(ctx):
    assert ctx.found_item
    # Must be a cleaner way to do it
    assert model("credit.control.run").get(ctx.found_item.id).state == 'done'

@then(u'the generated credit lines should have the following values')
def impl(ctx):
    def _row_to_dict(row):
        return dict((name, row[name]) for name in row.headings if row[name])
    rows = map(_row_to_dict, ctx.table)

    def _parse_date(value):
        return time.strftime(value) if '%' in value else value

    for row in rows:
        account = model('account.account').get(['name = %s' % row['account']])
        assert account, "no account named %s found" % row['account']
        import pdb; pdb.set_trace()

        policy = model('credit.control.policy').get(['name = %s' % row['policy']])
        assert policy, "No policy %s found" % row['policy']
        partner = model('res.partner').get(['name = %s' % row['partner']])
        assert partner, "No partner %s found" % row['partner']
        move_line = model('account.move.line').get(['name = %s' % row['move line']])
        assert move_line, "No move line %s found" % row['move line']
        level = model('credit.control.policy.level').get(['name = %s' % row['policy level'], 'policy_id = %s' % policy.id])
        assert level, "No level % found" % row['policy level']
        domain = [['account_id', '=', account.id],
                  ['policy_id', '=', policy.id],
                  ['partner_id', '=', partner.id],
                  ['policy_level_id', '=', level.id],
                  ['amount_due', '=', row.get('amount due', 0.0)],
                  ['state', '=', row['state']],
                  ['level', '=', row.get('level', 0.0)],
                  ['channel', '=', row['channel']],
                  ['balance_due', '=', row.get('balance', 0.0)],
                  ['date_due', '=',  _parse_date(row['date due'])],
                  ['date', '=', _parse_date(row['date'])],
                  ]
        if row.get('currrency'):
            curreny = model('res.currency').get(['name = %s' % row['currency']])
            assert curreny, "No currency %s found" % row['currency']
            domain.append(('currency_id', '=', curreny.id))

        lines = model('credit.control.line').search(domain)
        assert lines, "no line found for %s" % repr(row)
        assert len(lines) == 1, "Too many lines found for %s" % repr(row)
    date_lines = model('credit.control.lines').search([('date', '=', ctx.found_item.date)])
    assert len(date_lines) == len(ctx.table), "Too many lines generated"

def open_invoice(ctx):
    assert ctx.found_item
    ctx.found_item._send('invoice_open')
    # _send refresh object
    assert ctx.found_item.state == 'open'

@then(u'I open the credit invoice')
def impl(ctx):
    open_invoice(ctx)

@given(u'I open the credit invoice')
def impl(ctx):
    open_invoice(ctx)
