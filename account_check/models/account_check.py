# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, AUTHORS file in root directory
##############################################################################
from openerp import fields, models, _, api
from openerp.exceptions import Warning
import logging
import openerp.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)


class account_check(models.Model):

    _name = 'account.check'
    _description = 'Account Check'
    _order = "id desc"
    _inherit = ['mail.thread']

    @api.model
    def _get_checkbook(self):
        journal_id = self._context.get('default_journal_id', False)
        check_type = self._context.get('default_type', False)
        if journal_id and check_type == 'issue':
            checkbooks = self.env['account.checkbook'].search(
                [('state', '=', 'active'), ('journal_id', '=', journal_id)])
            return checkbooks and checkbooks[0] or False

    @api.one
    @api.depends('number', 'checkbook_id', 'checkbook_id.padding')
    def _get_name(self):
        padding = self.checkbook_id and self.checkbook_id.padding or 8
        self.name = '%%0%sd' % padding % self.number

    @api.one
    @api.depends(
        'voucher_id',
        'voucher_id.partner_id',
        'type',
        'third_handed_voucher_id',
        'third_handed_voucher_id.partner_id',
    )
    def _get_destiny_partner(self):
        partner_id = False
        if self.type == 'third' and self.third_handed_voucher_id:
            partner_id = self.third_handed_voucher_id.partner_id.id
        elif self.type == 'issue':
            partner_id = self.voucher_id.partner_id.id
        self.destiny_partner_id = partner_id

    @api.one
    @api.depends(
        'voucher_id',
        'voucher_id.partner_id',
        'type',
    )
    def _get_source_partner(self):
        partner_id = False
        if self.type == 'third':
            partner_id = self.voucher_id.partner_id.id
        self.source_partner_id = partner_id

    name = fields.Char(
        compute='_get_name',
        string='Number'
    )
    number = fields.Integer(
        'Number',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    amount = fields.Float(
        'Amount',
        required=True,
        readonly=True,
        digits=dp.get_precision('Account'),
        states={'draft': [('readonly', False)]},
    )
    company_currency_amount = fields.Float(
        'Company Currency Amount',
        readonly=True,
        digits=dp.get_precision('Account'),
        help='This value is only set for those checks that has a different currency than the company one.'
    )
    voucher_id = fields.Many2one(
        'account.voucher',
        'Voucher',
        readonly=True,
        required=True
    )
    type = fields.Selection(
        related='voucher_id.journal_id.check_type',
        string='Type',
        readonly=True,
        store=True
    )
    journal_id = fields.Many2one(
        'account.journal',
        related='voucher_id.journal_id',
        string='Journal',
        readonly=True,
        store=True
    )
    issue_date = fields.Date(
        'Issue Date',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    payment_date = fields.Date(
        'Payment Date',
        readonly=True,
        help="Only if this check is post dated",
        states={'draft': [('readonly', False)]}
    )
    destiny_partner_id = fields.Many2one(
        'res.partner',
        compute='_get_destiny_partner',
        string='Destiny Partner'
    )
    user_id = fields.Many2one(
        'res.users',
        'User',
        readonly=True,
        default=lambda self: self.env.user,
    )
    clearing = fields.Selection((
        ('24', '24 hs'),
        ('48', '48 hs'),
        ('72', '72 hs'),
    ), 'Clearing',
        readonly=True,
        states={'draft': [('readonly', False)]})
    state = fields.Selection((
        ('draft', 'Draft'),
        ('holding', 'Holding'),
        ('deposited', 'Deposited'),
        ('handed', 'Handed'),
        ('rejected', 'Rejected'),
        ('debited', 'Debited'),
        ('cancel', 'Cancel'),
    ), 'State',
        required=True,
        track_visibility='onchange',
        default='draft'
    )
    supplier_reject_debit_note_id = fields.Many2one(
        'account.invoice',
        'Supplier Reject Debit Note',
        readonly=True,
    )
    expense_account_move_id = fields.Many2one(
        'account.move',
        'Expense Account Move',
        readonly=True
    )

    # Related fields
    company_id = fields.Many2one(
        'res.company',
        related='voucher_id.company_id',
        string='Company',
        store=True,
        readonly=True
    )

    # Issue Check
    issue_check_subtype = fields.Selection(
        related='checkbook_id.issue_check_subtype',
        string='Subtype',
        readonly=True,
        store=True
    )
    checkbook_id = fields.Many2one(
        'account.checkbook', 'Checkbook',
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=_get_checkbook,
    )
    debit_account_move_id = fields.Many2one(
        'account.move',
        'Debit Account Move',
        readonly=True)

    # Third check
    third_handed_voucher_id = fields.Many2one(
        'account.voucher',
        'Handed Voucher',
        readonly=True,)
    source_partner_id = fields.Many2one(
        'res.partner',
        compute='_get_source_partner',
        string='Source Partner'
    )
    customer_reject_debit_note_id = fields.Many2one(
        'account.invoice',
        'Customer Reject Debit Note',
        readonly=True
    )
    bank_id = fields.Many2one(
        'res.bank', 'Bank',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
        related='voucher_id.journal_id.currency',
    )
    vat = fields.Char(
        'Vat',
        size=11,
        states={'draft': [('readonly', False)]}
    )
    deposit_account_move_id = fields.Many2one(
        'account.move',
        'Deposit Account Move',
        readonly=True
    )
    # this one is used for check rejection
    deposit_account_id = fields.Many2one(
        'account.account',
        'Deposit Account',
        readonly=True
    )

    def _check_number_interval(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.type != 'issue' or (obj.checkbook_id and obj.checkbook_id.range_from <= obj.number <= obj.checkbook_id.range_to):
                return True
        return False

    def _check_number_issue(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.type == 'issue':
                same_number_check_ids = self.search(
                    cr, uid, [
                        ('id', '!=', obj.id),
                        ('number', '=', obj.number),
                        ('checkbook_id', '=', obj.checkbook_id.id)],
                    context=context)
                if same_number_check_ids:
                    return False
        return True

    def _check_number_third(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if obj.type == 'third':
                same_number_check_ids = self.search(
                    cr, uid, [
                        ('id', '!=', obj.id),
                        ('number', '=', obj.number),
                        ('voucher_id.partner_id', '=', obj.voucher_id.partner_id.id)],
                    context=context)
                if same_number_check_ids:
                    return False
        return True

    _constraints = [
        (_check_number_interval, 'Check Number Must be in Checkbook interval!', [
         'number', 'checkbook_id']),
        (_check_number_issue, 'Check Number must be unique per Checkbook!',
         ['number', 'checkbook_id']),
        (_check_number_third, 'Check Number must be unique per Customer and Bank!', [
         'number', 'bank_id']),
    ]

    @api.one
    @api.onchange('issue_date', 'payment_date')
    def onchange_date(self):
        res = {}
        if self.issue_date and self.payment_date and self.issue_date > self.payment_date:
            res = {'value': {'payment_date': False}}
            res.update({'warning': {
                'title': _('Error !'),
                'message': _('Payment Date must be greater than Issue Date')}})
        return res

    @api.one
    def unlink(self):
        if self.state not in ('draft'):
            raise Warning(
                _('The Check must be in draft state for unlink !'))
        return super(account_check, self).unlink()

    @api.one
    @api.onchange('checkbook_id')
    def onchange_checkbook(self):
        if self.checkbook_id:
            self.number = self.checkbook_id.next_check_number

    @api.multi
    def action_cancel_draft(self):
        # go from canceled state to draft state
        self.write({'state': 'draft'})
        self.delete_workflow()
        self.create_workflow()
        return True

    @api.multi
    def action_hold(self):
        self.write({'state': 'holding'})
        return True

    @api.multi
    def action_deposit(self):
        self.write({'state': 'deposited'})
        return True

    @api.multi
    def action_hand(self):
        self.write({'state': 'handed'})
        return True

    @api.multi
    def action_reject(self):
        self.write({'state': 'rejected'})
        return True

    @api.multi
    def action_debit(self):
        self.write({'state': 'debited'})
        return True

    @api.multi
    def action_cancel_rejection(self):
        for check in self:
            if check.customer_reject_debit_note_id:
                raise Warning(
                    _('To cancel a rejection you must first delete the customer reject debit note!'))
            if check.supplier_reject_debit_note_id:
                raise Warning(
                    _('To cancel a rejection you must first delete the supplier reject debit note!'))
            if check.expense_account_move_id:
                raise Warning(
                    _('To cancel a rejection you must first delete Expense Account Move!'))
            check.signal_workflow('cancel_rejection')
        return True

    @api.multi
    def action_cancel_debit(self):
        for check in self:
            if check.debit_account_move_id:
                raise Warning(
                    _('To cancel a debit you must first delete Debit Account Move!'))
            check.signal_workflow('debited_handed')
        return True

    @api.multi
    def action_cancel_deposit(self):
        for check in self:
            if check.deposit_account_move_id:
                raise Warning(
                    _('To cancel a deposit you must first delete the Deposit Account Move!'))
            check.signal_workflow('cancel_deposit')
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True
