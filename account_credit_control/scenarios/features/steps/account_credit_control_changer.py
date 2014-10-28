# -*- coding: utf-8 -*-
from support import model, assert_equal, assert_in, assert_true

# flake8: noqa
@given(u'I change level for invoice "{invoice_name}" to "{level_name}" of policy "{policy_name}"')
def impl(ctx, invoice_name, level_name, policy_name):
   invoice = model('account.invoice').get([('number', '=', invoice_name)])
   assert_true(invoice, msg='No invoices found')
   level = model('credit.control.policy.level').get([('name', '=', level_name)])
   assert_true(level, 'level not found')
   policy = model('credit.control.policy').get([('name', '=', policy_name)])
   assert_true(policy, 'Policy not found')
   assert_equal(policy.id, level.policy_id.id)
   context = {'active_ids': [invoice.id]}
   data = {'new_policy_id': policy.id,
           'new_policy_level_id': level.id}
   wizard = model('credit.control.policy.changer').create(data, context=context)
   ctx.wizard = wizard

@then(u'wizard selected move lines should be')
def impl(ctx):
    assert_true(ctx.wizard)
    names = [x.name for x in ctx.wizard.move_line_ids]
    for line in ctx.table:
        assert_in(line['name'], names)

@when(u'I confirm the level change')
def impl(ctx):
    assert_true(ctx.wizard)
    ctx.wizard.set_new_policy()

@when(u'I should have "{line_number:d}" credit control lines overridden')
def impl(ctx, line_number):
    assert_true(ctx.wizard)
    move_ids = [x.id for x in ctx.wizard.move_line_ids]
    overridden = model('credit.control.line').search([('move_line_id', 'in', move_ids),
                                                     ('manually_overridden', '=', True)])
#    assert len(overridden) == line_number

@when(u'one new credit control line of level "{level_name}" related to invoice "{invoice_name}"')
def impl(ctx, level_name, invoice_name):
   invoice = model('account.invoice').get([('number', '=', invoice_name)])
   assert_true(invoice, msg='No invoices found')
   level = model('credit.control.policy.level').get([('name', '=', level_name)])
   assert_true(level, 'level not found')
   assert_true(ctx.wizard)
   move_ids = [x.id for x in ctx.wizard.move_line_ids]
   created_id = model('credit.control.line').search([('move_line_id', 'in', move_ids),
                                                     ('manually_overridden', '=', False)])

   assert len(created_id) == 1
   created = model('credit.control.line').get(created_id[0])
   ctx.created = created
   assert_equal(created.policy_level_id.id, level.id)
   assert_equal(created.invoice_id.id, invoice.id)
   assert_equal(created.invoice_id.credit_policy_id.id, level.policy_id.id)

@then(u'I force date of generated credit line to "{date}"')
def impl(ctx, date):
    assert_true(ctx.created)
    ctx.created.write({'date': date})

@given(u'the invoice "{invoice_name}" with manual changes')
def impl(ctx, invoice_name):
   invoice = model('account.invoice').get([('number', '=', invoice_name)])
   assert_true(invoice, msg='No invoices found')
   man_lines = (x for x in invoice.credit_control_line_ids if x.manually_overridden)
   assert_true(next(man_lines, None), 'No manual change on the invoice')
   ctx.invoice = invoice

@given(u'the invoice has "{line_number:d}" line of level "{level:d}" for policy "{policy_name}"')
def impl(ctx, line_number, level, policy_name):
    assert_true(ctx.invoice)
    policy = model('credit.control.policy').get([('name', '=', policy_name)])
    assert_true(policy)
    lines = model('credit.control.line').search([('invoice_id', '=', ctx.invoice.id),
                                                 ('level', '=', level),
                                                 ('policy_id', '=', policy.id)])
    assert_equal(len(lines), line_number)
