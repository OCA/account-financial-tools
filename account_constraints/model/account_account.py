# -*- encoding: utf-8 -*-
# noqa: skip pep8 since code infra is correction of standard account module
# flake8: noqa
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models


class account_account(models.Model):
    """
    disable this _check_account_type constraint
    cf. https://github.com/odoo/odoo/pull/4512
    """
    _inherit = 'account.account'

    def _check_account_type(self, cr, uid, ids, context=None):
        """
        # We disable that constraint that makes impossible to use balance for receivable - payable

        for account in self.browse(cr, uid, ids, context=context):
            if account.type in ('receivable', 'payable') and account.user_type.close_method != 'unreconciled':
                return False
        """
        return True

    _constraints = [
        # the constraint below has been disabled
        (_check_account_type, 'Configuration Error!\nYou cannot select an account type with a deferral method different of "Unreconciled" for accounts with internal type "Payable/Receivable".', ['user_type','type']),
    ]
