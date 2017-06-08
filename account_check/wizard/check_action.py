# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, AUTHORS file in root directory
##############################################################################
from openerp.exceptions import Warning
from openerp import models, fields, api, _


class account_check_action(models.TransientModel):
    _name = 'account.check.action'

    @api.model
    def _get_company_id(self):
        active_ids = self._context.get('active_ids', [])
        checks = self.env['account.check'].browse(active_ids)
        company_ids = [x.company_id.id for x in checks]
        if len(set(company_ids)) > 1:
            raise Warning(_('All checks must be from the same company!'))
        return self.env['res.company'].search(
            [('id', 'in', company_ids)], limit=1)

    account_id = fields.Many2one(
        'account.account',
         'Account',
        domain=[('type', 'in', ['other', 'liquidity'])])
    date = fields.Date(
        'Debit Date', 
        required=True, 
        default=fields.Date.context_today)
    action_type = fields.Char(
        'Action type passed on the context', 
        required=True)
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=_get_company_id
    )

    def action_confirm(self, cr, uid, ids, context=None):
        check_obj = self.pool.get('account.check')
        move_line_obj = self.pool.get('account.move.line')
        wizard = self.browse(cr, uid, ids[0], context=context)
        context['company_id'] = wizard.company_id.id

        # used to get correct ir properties
        context['force_company'] = wizard.company_id.id

        period_id = self.pool.get('account.period').find(
            cr, uid, wizard.date, context=context)[0]
        if context is None:
            context = {}

        record_ids = context.get('active_ids', [])
        for check in check_obj.browse(cr, uid, record_ids, context=context):
            if check.type == 'third':
                if check.state != 'holding':
                    raise Warning(
                        _('The selected checks must be in holding state.'))
                if wizard.action_type == 'debit':
                    raise Warning(_('You can not debit a Third Check.'))
            elif check.type == 'issue':
                if check.state != 'handed':
                    raise Warning(
                        _('The selected checks must be in handed state.'))
                if wizard.action_type == 'deposit':
                    raise Warning(_('You can not deposit a Issue Check.'))

            if wizard.action_type == 'deposit':
                # TODO: tal vez la cuenta de deposito del cheque deberia salir
                # de la seleccion de un jorunal y el journal tambien.
                ref = _('Deposit Check Nr. ')
                check_move_field = 'deposit_account_move_id'
                journal = check.voucher_id.journal_id
                debit_account_id = wizard.account_id.id
                partner = check.source_partner_id.id,
                credit_account_id = check.voucher_id.journal_id.default_credit_account_id.id
                check_vals = {'deposit_account_id': debit_account_id}
                signal = 'holding_deposited'
            elif wizard.action_type == 'debit':
                ref = _('Debit Check Nr. ')
                check_move_field = 'debit_account_move_id'
                journal = check.checkbook_id.debit_journal_id
                partner = check.destiny_partner_id.id
                credit_account_id = journal.default_debit_account_id.id
                debit_account_id = check.voucher_id.journal_id.default_credit_account_id.id
                check_vals = {}
                signal = 'handed_debited'

            name = self.pool.get('ir.sequence').next_by_id(
                cr, uid, journal.sequence_id.id, context=context)
            ref += check.name
            move_id = self.pool.get('account.move').create(cr, uid, {
                'name': name,
                'journal_id': journal.id,
                'period_id': period_id,
                'date': wizard.date,
                'ref':  ref,
            })
            move_line_obj.create(cr, uid, {
                'name': name,
                'account_id': debit_account_id,
                'partner_id': partner,
                'move_id': move_id,
                'debit': check.company_currency_amount or check.amount,
                'amount_currency': check.company_currency_amount and check.amount or False,
                'ref': ref,
            })
            move_line_obj.create(cr, uid, {
                'name': name,
                'account_id': credit_account_id,
                'partner_id': partner,
                'move_id': move_id,
                'credit': check.company_currency_amount or check.amount,
                'amount_currency': check.company_currency_amount and -1 * check.amount or False,
                'ref': ref,
            })

            check_vals[check_move_field] = move_id
            check.write(check_vals)
            check.signal_workflow(signal)
        self.pool.get('account.move').write(
            cr, uid, [move_id], {'state': 'posted', }, context=context)

        return {}
