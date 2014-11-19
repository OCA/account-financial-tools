# -*- coding: utf-8 -*-
##############################################################################
#
#   Author Vincent Renaville/Joel Grand-Guillaume.Copyright 2012 Camptocamp SA
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        """Set move line in draft state after creating them."""
        res = super(AccountInvoice, self).action_move_create()
        for inv in self:
            if inv.move_id:
                inv.move_id.state = 'draft'
        return res


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def button_cancel(self):
        """ We rewrite function button_cancel, to allow invoice or bank
        statement with linked draft moved
        to be canceled """
        for line in self:
            if line.state == 'draft':
                continue
            else:
                if not line.journal_id.update_posted:
                    raise exceptions.Warning(
                        _('You cannot modify a posted entry of this journal.'
                          'First you should set the journal to allow'
                          ' cancelling entries.'))
        if self:
            self._cr.execute('UPDATE account_move '
                             'SET state=%s '
                             'WHERE id IN %s', ('draft', self.ids,))
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
