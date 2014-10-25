# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account partner required module for OpenERP
#    Copyright (C) 2014 Acsone (http://acsone.eu).
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
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

from openerp.osv import orm, fields
from openerp.tools.translate import _


class account_account_type(orm.Model):
    _inherit = "account.account.type"

    def _get_policies(self, cr, uid, context=None):
        """This is the method to be inherited for adding policies"""
        return [('optional', 'Optional'),
                ('always', 'Always'),
                ('never', 'Never')]

    def __get_policies(self, cr, uid, context=None):
        """ Call method which can be inherited """
        return self._get_policies(cr, uid, context=context)

    _columns = {
        'partner_policy': fields.selection(
            __get_policies,
            'Policy for partner field',
            required=True,
            help="Set the policy for the partner field : if you select "
                 "'Optional', the accountant is free to put a partner "
                 "on an account move line with this type of account ; "
                 "if you select 'Always', the accountant will get an error "
                 "message if there is no partner ; if you select 'Never', "
                 "the accountant will get an error message if a partner "
                 "is present."),
    }

    _defaults = {
        'partner_policy': 'optional',
    }


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def _get_partner_policy(self, cr, uid, account, context=None):
        """ Extension point to obtain analytic policy for an account """
        return account.user_type.partner_policy

    def _check_partner_required_msg(self, cr, uid, ids, context=None):
        for move_line in self.browse(cr, uid, ids, context):
            if move_line.debit == 0 and move_line.credit == 0:
                continue
            policy = self._get_partner_policy(cr, uid,
                                              move_line.account_id,
                                              context=context)
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

    def _check_partner_required(self, cr, uid, ids, context=None):
        return not self._check_partner_required_msg(cr, uid, ids,
                                                    context=context)

    _constraints = [
        (_check_partner_required,
         _check_partner_required_msg,
         ['partner_id', 'account_id']),
    ]
