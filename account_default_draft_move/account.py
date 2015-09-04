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

from openerp import models, api, fields, exceptions, _
from openerp.tools.safe_eval import safe_eval


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_move_create(self):
        """Set move line in draft state after creating them."""
        res = super(AccountInvoice, self).action_move_create()
        use_journal_setting = safe_eval(self.env['ir.config_parameter'].
                                        get_param('use_journal_setting',
                                                  default="False"))
        for inv in self:
            if inv.move_id:
                if use_journal_setting and inv.move_id.journal_id.entry_posted:
                    continue
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
                             'WHERE id IN %s', ('draft', tuple(self.ids)))
        return True

    @api.multi
    def _is_update_posted(self):
        ir_module = self.env['ir.module.module']
        can_cancel = ir_module.search([('name', '=', 'account_cancel'),
                                       ('state', '=', 'installed')])
        for move in self:
            move.update_posted = can_cancel and move.journal_id.update_posted

    update_posted = fields.Boolean(compute='_is_update_posted',
                                   string='Allow Cancelling Entries')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    # update help of entry_posted flag
    entry_posted = fields.Boolean(
        string='Skip \'Draft\' State',
        help="""Check this box if you don't want new journal entries
to pass through the 'draft' state and instead goes directly
to the 'posted state' without any manual validation.""")
