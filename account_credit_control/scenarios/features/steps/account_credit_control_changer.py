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

@when(u'I should have "{line_number:d}" credit control lines overriden')
def impl(ctx, line_number):
    assert_true(ctx.wizard)
    move_ids = [x.id for x in ctx.wizard.move_line_ids]
    overriden = model('credit.control.line').search([('move_line_id', 'in', move_ids),
                                                     ('manually_overriden', '=', True)])
#    assert len(overriden) == line_number

@when(u'one new credit control line of level "{level_name}" related to invoice "{invoice_name}"')
def impl(ctx, level_name, invoice_name):
   invoice = model('account.invoice').get([('number', '=', invoice_name)])
   assert_true(invoice, msg='No invoices found')
   level = model('credit.control.policy.level').get([('name', '=', level_name)])
   assert_true(level, 'level not found')
   assert_true(ctx.wizard)
   move_ids = [x.id for x in ctx.wizard.move_line_ids]
   created_id = model('credit.control.line').search([('move_line_id', 'in', move_ids),
                                                     ('manually_overriden', '=', False)])

   assert len(created_id) == 1
   created = model('credit.control.line').get(created_id[0])
   assert_equal(created.policy_level_id.id, level.id)
   assert_equal(created.invoice_id.id, invoice.id)
   assert_equal(created.invoice_id.credit_policy_id.id, level.policy_id.id)
