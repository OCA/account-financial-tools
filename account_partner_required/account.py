# -*- coding: utf-8 -*-
# Copyright 2014 Acsone (http://acsone.eu).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _


class AccountAccountType(models.Model):
    _inherit = "account.account.type"

    def _get_policies(self):
        """This is the method to be inherited for adding policies"""
        return [('optional', _('Optional')),
                ('always', _('Always')),
                ('never', _('Never'))]

    partner_policy = fields.Selection(
        lambda self: self._get_policies(),
        'Policy for partner field',
        required=True,
        help="Set the policy for the partner field : if you select "
             "'Optional', the accountant is free to put a partner "
             "on an account move line with this type of account ; "
             "if you select 'Always', the accountant will get an error "
             "message if there is no partner ; if you select 'Never', "
             "the accountant will get an error message if a partner "
             "is present.",
        default='optional',
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_partner_policy(self, account):
        """ Extension point to obtain analytic policy for an account """
        return account.user_type.partner_policy

    @api.multi
    def _check_partner_required_msg(self):
        for move_line in self:
            if move_line.debit == 0 and move_line.credit == 0:
                continue
            policy = self._get_partner_policy(move_line.account_id)
            if policy == 'always' and not move_line.partner_id:
                return _("Partner policy is set to 'Always' "
                         "with account %s '%s' but the "
                         "partner is missing in the account "
                         "move line with label '%s'." %
                         (move_line.account_id.code,
                          move_line.account_id.name,
                          move_line.name))
            elif policy == 'never' and move_line.partner_id:
                return _("Partner policy is set to 'Never' "
                         "with account %s '%s' but the "
                         "account move line with label '%s' "
                         "has a partner '%s'." %
                         (move_line.account_id.code,
                          move_line.account_id.name,
                          move_line.name,
                          move_line.partner_id.name))

    @api.multi
    def _check_partner_required(self):
        return not self._check_partner_required_msg()

    _constraints = [
        (_check_partner_required,
         _check_partner_required_msg,
         ['partner_id', 'account_id', 'debit', 'credit']),
    ]
