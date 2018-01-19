# Copyright 2012-2017 Camptocamp SA
# Copyright 2017 Okia SPRL (https://okia.be)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class CreditControlPolicyChanger(models.TransientModel):
    """ Wizard that is run from invoices and allows to set manually a policy
    Policy are actually apply to related move lines availabe
    in selection widget

    """
    _name = "credit.control.policy.changer"

    @api.model
    def _default_move_lines(self):
        """ Get default lines for fields move_line_ids
        of wizard. Only take lines that are on the same account
        and move of the invoice and not reconciled

        :return: list of compliant move lines

        """
        context = self.env.context
        active_ids = context.get('active_ids')
        invoice_obj = self.env['account.invoice']
        if not active_ids:
            return False
        selected_lines = self.env['account.move.line']
        for invoice in invoice_obj.browse(active_ids):
            if invoice.type in ('in_invoice', 'in_refund', 'out_refund'):
                raise UserError(_('Please use wizard on customer invoices'))

            domain = [('account_id', '=', invoice.account_id.id),
                      ('move_id', '=', invoice.move_id.id),
                      ('reconciled', '=', False)]
            move_lines = selected_lines.search(domain)
            selected_lines |= move_lines
        return selected_lines

    new_policy_id = fields.Many2one('credit.control.policy',
                                    string='New Policy to Apply',
                                    required=True)
    new_policy_level_id = fields.Many2one('credit.control.policy.level',
                                          string='New level to apply',
                                          required=True)
    # Only used to provide dynamic filtering on form
    do_nothing = fields.Boolean(string='No follow  policy')
    move_line_ids = fields.Many2many('account.move.line',
                                     rel='credit_changer_ml_rel',
                                     string='Move line to change',
                                     default=lambda self:
                                         self._default_move_lines())

    @api.onchange('new_policy_level_id')
    def onchange_policy_id(self):
        if not self.new_policy_id:
            return
        self.do_nothing = self.new_policy_id.do_nothing

    @api.model
    @api.returns('credit.control.line')
    def _mark_as_overridden(self, move_lines):
        """ Mark `move_lines` related credit control line as overridden
        This is done by setting manually_overridden fields to True

        :param move_lines: move line to mark as overridden
        :return: list of credit lines that where marked as overridden
        """
        credit_obj = self.env['credit.control.line']
        domain = [('move_line_id', 'in', move_lines.ids)]
        credit_lines = credit_obj.search(domain)
        credit_lines.write({'manually_overridden': True})
        return credit_lines

    @api.model
    def _set_invoice_policy(self, move_lines, policy):
        """ Force policy on invoice """
        invoices = move_lines.mapped('invoice_id')
        invoices.write({'credit_policy_id': policy.id})

    @api.model
    def _check_accounts_policies(self, lines, policy):
        accounts = set(line.account_id for line in lines)
        for account in accounts:
            policy.check_policy_against_account(account)
        return True

    @api.multi
    def set_new_policy(self):
        """ Set new policy on an invoice.

        This is done by creating a new credit control line
        related to the move line and the policy setted in
        the wizard form

        :return: ir.actions.act_windows dict

        """
        self.ensure_one()
        credit_line_obj = self.env['credit.control.line']

        controlling_date = fields.date.today()
        self._check_accounts_policies(self.move_line_ids, self.new_policy_id)
        self._mark_as_overridden(self.move_line_ids)
        # As disscused with business expert
        # draft lines should be passed to ignored
        # if same level as the new one
        # As it is a manual action
        # We also ignore rounding tolerance
        create = credit_line_obj.create_or_update_from_mv_lines
        generated_lines = create(self.move_line_ids,
                                 self.new_policy_level_id,
                                 controlling_date,
                                 check_tolerance=False)
        self._set_invoice_policy(self.move_line_ids, self.new_policy_id)

        if not generated_lines:
            return {'type': 'ir.actions.act_window_close'}

        action_ref = 'account_credit_control.credit_control_line_action'
        action = self.env.ref(action_ref)
        action = action.read()[0]
        action['domain'] = [('id', 'in', generated_lines.ids)]
        return action
