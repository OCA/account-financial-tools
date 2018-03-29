# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class CreditControlLine(models.Model):
    """ A credit control line describes an amount due by a customer for a due date.

    A line is created once the due date of the payment is exceeded.
    It is created in "draft" and some actions are available (send by email,
    print, ...)
    """

    _name = "credit.control.line"
    _description = "A credit control line"
    _rec_name = "id"
    _order = "date DESC"

    date = fields.Date(string='Controlling date',
                       required=True,
                       index=True)
    # maturity date of related move line we do not use
    # a related field in order to
    # allow manual changes
    date_due = fields.Date(string='Due date',
                           required=True,
                           readonly=True,
                           states={'draft': [('readonly', False)]})
    date_entry = fields.Date(string='Entry date',
                             related='move_line_id.date',
                             store=True,
                             readonly=True)
    date_sent = fields.Date(string='Sent date',
                            readonly=True,
                            states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'),
                              ('ignored', 'Ignored'),
                              ('to_be_sent', 'Ready To Send'),
                              ('sent', 'Done'),
                              ('error', 'Error'),
                              ('email_error', 'Emailing Error')],
                             required=True,
                             readonly=True,
                             default='draft',
                             help="Draft lines need to be triaged.\n"
                                  "Ignored lines are lines for which we do "
                                  "not want to send something.\n"
                                  "Draft and ignored lines will be "
                                  "generated again on the next run.")
    channel = fields.Selection([('letter', 'Letter'),
                                ('email', 'Email')],
                               required=True,
                               readonly=True,
                               states={'draft': [('readonly', False)]})
    invoice_id = fields.Many2one('account.invoice',
                                 string='Invoice',
                                 readonly=True)
    partner_id = fields.Many2one('res.partner',
                                 string='Partner',
                                 required=True)
    amount_due = fields.Float(string='Due Amount Tax incl.',
                              required=True, readonly=True)
    balance_due = fields.Float(string='Due balance', required=True,
                               readonly=True)
    mail_message_id = fields.Many2one('mail.mail', string='Sent Email',
                                      readonly=True)
    move_line_id = fields.Many2one('account.move.line',
                                   string='Move line',
                                   required=True,
                                   readonly=True)
    account_id = fields.Many2one('account.account',
                                 related='move_line_id.account_id',
                                 store=True,
                                 readonly=True)
    currency_id = fields.Many2one('res.currency',
                                  related='move_line_id.currency_id',
                                  store=True,
                                  readonly=True)
    company_id = fields.Many2one('res.company',
                                 related='move_line_id.company_id',
                                 store=True,
                                 readonly=True)
    # we can allow a manual change of policy in draft state
    policy_level_id = fields.Many2one('credit.control.policy.level',
                                      string='Overdue Level',
                                      required=True,
                                      readonly=True,
                                      states={'draft': [('readonly', False)]})
    policy_id = fields.Many2one('credit.control.policy',
                                related='policy_level_id.policy_id',
                                store=True,
                                readonly=True)
    level = fields.Integer(related='policy_level_id.level',
                           store=True,
                           readonly=True)
    manually_overridden = fields.Boolean()
    run_id = fields.Many2one(comodel_name='credit.control.run',
                             string='Source')
    manual_followup = fields.Boolean()

    @api.model
    def _prepare_from_move_line(self, move_line, level, controlling_date,
                                open_amount):
        """ Create credit control line """
        data = {}
        data['date'] = controlling_date
        data['date_due'] = move_line.date_maturity
        data['state'] = 'draft'
        data['channel'] = level.channel
        data['invoice_id'] = (move_line.invoice_id.id if
                              move_line.invoice_id else False)
        data['partner_id'] = move_line.partner_id.id
        data['amount_due'] = (move_line.amount_currency or move_line.debit or
                              move_line.credit)
        data['balance_due'] = open_amount
        data['policy_level_id'] = level.id
        data['move_line_id'] = move_line.id
        return data

    @api.model
    def create_or_update_from_mv_lines(self, lines, level, controlling_date,
                                       check_tolerance=True):
        """ Create or update line based on levels

        if check_tolerance is true credit line will not be
        created if open amount is too small.
        eg. we do not want to send a letter for 10 cents
        of open amount.

        :param lines: move.line id recordset
        :param level: credit.control.policy.level record
        :param controlling_date: date string of the credit controlling date.
                                 Generally it should be the same
                                 as create date
        :param check_tolerance: boolean if True credit line
                                will not be generated if open amount
                                is smaller than company defined
                                tolerance

        :returns: recordset of created credit lines
        """
        currency_obj = self.env['res.currency']
        user = self.env.user
        currencies = currency_obj.search([])

        tolerance = {}
        tolerance_base = user.company_id.credit_control_tolerance
        user_currency = user.company_id.currency_id
        for currency in currencies:
            tolerance[currency.id] = currency.compute(tolerance_base,
                                                      user_currency)

        new_lines = self.browse()
        for move_line in lines:
            ml_currency = move_line.currency_id
            if ml_currency and ml_currency != user_currency:
                open_amount = move_line.amount_residual_currency
            else:
                open_amount = move_line.amount_residual
            cur_tolerance = tolerance.get(move_line.currency_id.id,
                                          tolerance_base)
            if check_tolerance and open_amount < cur_tolerance:
                continue
            vals = self._prepare_from_move_line(move_line,
                                                level,
                                                controlling_date,
                                                open_amount)
            line = self.create(vals)
            new_lines |= line

            # when we have lines generated earlier in draft,
            # on the same level, it means that we have left
            # them, so they are to be considered as ignored
            previous_drafts = self.search([('move_line_id', '=', move_line.id),
                                           ('policy_level_id', '=', level.id),
                                           ('state', '=', 'draft'),
                                           ('id', '!=', line.id)])
            if previous_drafts:
                previous_drafts.write({'state': 'ignored'})

        return new_lines

    @api.multi
    def unlink(self):
        for line in self:
            if line.state != 'draft':
                raise UserError(
                    _('You are not allowed to delete a credit control '
                      'line that is not in draft state.')
                )

        return super(CreditControlLine, self).unlink()

    @api.multi
    def write(self, values):
        res = super(CreditControlLine, self).write(values)
        if 'manual_followup' in values:
            self.partner_id.write({
                'manual_followup': values.get('manual_followup'),
            })
        return res

    @api.model
    def create(self, values):
        line = super(CreditControlLine, self).create(values)
        line.manual_followup = line.partner_id.manual_followup
        return line
