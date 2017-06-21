# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    locked = fields.Boolean('Locked', readonly=True)

    @api.multi
    def write(self, vals):
        for move in self:
            if move.locked:
                raise exceptions.UserError(_('Move Locked! %s') % (move.name))
        return super(AccountMove, self).write(vals)

    @api.multi
    def unlink(self):
        for move in self:
            if move.locked:
                raise exceptions.UserError(_('Move Locked! %s') % (move.name))
        return super(AccountMove, self).unlink()

    @api.multi
    def button_cancel(self):
        # Cancel a move was done directly in SQL
        # so we need to test manualy if the move is locked
        for move in self:
            if move.locked:
                raise exceptions.UserError(_('Move Locked! %s') % (move.name))
        return super(AccountMove, self).button_cancel()
