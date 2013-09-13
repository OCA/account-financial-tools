# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2013 Camptocamp SA
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
from openerp.osv import orm


class account_move(orm.Model):
    """redefine account move create to bypass orm
    if async_bypass_create is True in context"""

    _inherit = "account.move"

    def _bypass_create(self, cr, uid, vals, context=None):
        pass

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if context.get('async_bypass_create'):
            return self._bypass_create(cr, uid, vals, context=context)
        return super(account_move, self).create(cr, uid, vals, context=context)


class account_move_line(orm.Model):
    """redefine account move line create to bypass orm
    if async_bypass_create is True in context"""

    _inherit = "account.move.line"

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if context.get('async_bypass_create'):
                return self._bypass_create(cr, uid, vals, context=context)
        return super(account_move_line, self).create(cr, uid, vals, context=context)

    def _bypass_create(self, cr, uid, vals, context=None):
        pass
