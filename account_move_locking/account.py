# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville.
#    Copyright 2015 Camptocamp SA
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
##############################################################################

from openerp import models, fields, api, exceptions, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    locked = fields.Boolean('Locked', readonly=True)

    @api.multi
    def write(self, vals):
        for move in self:
            if move.locked:
                raise exceptions.Warning(_('Move Locked!'),
                                         move.name)
        return super(AccountMove, self).write(vals)

    @api.multi
    def unlink(self):
        for move in self:
            if move.locked:
                raise exceptions.Warning(_('Move Locked!'),
                                         move.name)
        return super(AccountMove, self).unlink()

    @api.multi
    def button_cancel(self):
        # Cancel a move was done directly in SQL
        # so we need to test manualy if the move is locked
        for move in self:
            if move.locked:
                raise exceptions.Warning(_('Move Locked!'),
                                         move.name)
        return super(AccountMove, self).button_cancel()
