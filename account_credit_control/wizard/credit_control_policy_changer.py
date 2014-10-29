# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2014 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from openerp import models, fields, api, _
logger = logging.getLogger(__name__)


class credit_control_policy_changer(models.TransientModel):
    """ Wizard that is run from invoices and allows to set manually a policy
    Policy are actually apply to related move lines availabe
    in selection widget

    """
    _name = "credit.control.policy.changer"

    new_policy_id = fields.Many2one('credit.control.policy',
                                    string='New Policy to Apply',
                                    required=True)
    new_policy_level_id = fields.Many2one('credit.control.policy.level',
                                          string='New level to apply',
                                          required=True)
    # Only used to provide dynamic filtering on form
    do_nothing = fields.Boolean(string='No follow  policy')

    @api.model
    def _get_default_lines(self):
        """ Get default lines for fields move_line_ids
        of wizard. Only take lines that are on the same account
        and move of the invoice and not reconciled

        :return: list of compliant move lines

        """
        context = self.env.context
        active_ids = context.get('active_ids')
        invoice_obj = self.env['account.invoice']
        move_line_obj = self.env['account.move.line']
        if not active_ids:
            return False
        selected_lines = move_line_obj.browse()
        for invoice in invoice_obj.browse(active_ids):
            if invoice.type in ('in_invoice', 'in_refund', 'out_refund'):
                raise api.Warning(_('Please use wizard on customer invoices'))

            domain = [('account_id', '=', invoice.account_id.id),
                      ('move_id', '=', invoice.move_id.id),
                      ('reconcile_id', '=', False)]
            move_lines = move_line_obj.search(domain)
            selected_lines |= move_lines
        return selected_lines

    move_line_ids = fields.Many2many('account.move.line',
                                     rel='credit_changer_ml_rel',
                                     string='Move line to change',
                                     default=_get_default_lines)

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
        invoice_obj = self.env['account.invoice']
        invoice_ids = set(line.invoice.id for line in move_lines
                          if line.invoice)
        invoices = invoice_obj.browse(invoice_ids)
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
