# -*- coding: utf-8 -*-
# flake8: noqa
import time
from behave import given, when
from support import model, assert_equal

@given(u'I configure the following accounts on the credit control policy with oid: "{policy_oid}"')
def impl(ctx, policy_oid):
    policy = model('credit.control.policy').get(policy_oid)
    assert policy, 'No policy % found' % policy_oid
    acc_obj = model('account.account')
    accounts = []
    for row in ctx.table:
        acc = acc_obj.get(['code = %s' % row['account code']])
        assert acc,  "Account with code %s not found" % row['account code']
        accounts.append(acc)
    policy.write({'account_ids': [x.id for x in accounts]})


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

        policy = model('credit.control.policy').get(['name = %s' % row['policy']])
        assert policy, "No policy %s found" % row['policy']

        partner = model('res.partner').get(['name = %s' % row['partner']])
        assert partner, "No partner %s found" % row['partner']

        maturity_date = _parse_date(row['date due'])
        move_line = model('account.move.line').get(['name = %s' % row['move line'],
                                                    'date_maturity = %s' % maturity_date])
        assert move_line, "No move line %s found" % row['move line']

        level = model('credit.control.policy.level').get(['name = %s' % row['policy level'],
                                                          'policy_id = %s' % policy.id])
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
                  ['move_line_id', '=', move_line.id],
                  ]
        if row.get('currency'):
            curreny = model('res.currency').get(['name = %s' % row['currency']])
            assert curreny, "No currency %s found" % row['currency']
            domain.append(('currency_id', '=', curreny.id))

        lines = model('credit.control.line').search(domain)
        assert lines, "no line found for %s" % repr(row)
        assert len(lines) == 1, "Too many lines found for %s" % repr(row)
    date_lines = model('credit.control.line').search([('date', '=', ctx.found_item.date)])
    assert len(date_lines) == len(ctx.table.rows), "Too many lines generated"


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

@given(u'there is "{state}" credit lines')
def impl(ctx, state):
    assert model('credit.control.line').search(['state = %s' % state])

@given(u'I mark all draft email to state "{state}"')
def impl(ctx, state):
    wiz = model('credit.control.marker').create({'name': state})
    lines = model('credit.control.line').search([('state', '=', 'draft')])
    assert lines
    ctx.lines = lines
    wiz.write({'line_ids': lines})
    wiz.mark_lines()

@then(u'the draft line should be in state "{state}"')
def impl(ctx, state):
    assert ctx.lines
    lines = model('credit.control.line').search([('state', '!=', state),
                                                 ('id', 'in', ctx.lines)])
    assert not lines

@given(u'I ignore the "{partner}" credit line at level "{level:d}" for move line "{move_line_name}" with amount "{amount:f}"')
def impl(ctx, partner, level, move_line_name, amount):
    print ctx, partner, level, move_line_name, amount
    to_ignore = model('credit.control.line').search([('partner_id.name', '=', partner),
                                                     ('level', '=', level),
                                                     ('amount_due', '=', amount),
                                                     ('move_line_id.name', '=', move_line_name)])
    assert to_ignore
    wiz = model('credit.control.marker').create({'name': 'ignored'})
    ctx.lines = to_ignore
    wiz.write({'line_ids': to_ignore})
    wiz.mark_lines()
    assert model('credit.control.line').get(to_ignore[0]).state == 'ignored'

@given(u'I have for "{partner}" "{number:d}" credit lines at level "{level:d}" for move line "{move_line_name}" with amount "{amount:f}" respectively in state "draft" and "ignored"')
def impl(ctx, partner, number, level, move_line_name, amount):
    to_check = model('credit.control.line').search([('partner_id.name', '=', partner),
                                                    ('level', '=', level),
                                                    ('amount_due', '=', amount),
                                                    ('move_line_id.name', '=', move_line_name),
                                                    ('state', 'in', ('draft', 'ignored'))])
    assert_equal(len(to_check), int(number), msg="More than %s found" % number)
    lines = model('credit.control.line').browse(to_check)
    assert set(['ignored', 'draft']) == set(lines.state)
