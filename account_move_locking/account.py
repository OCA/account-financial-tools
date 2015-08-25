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

from openerp.osv import fields, orm
from tools.translate import _


class AccountMove(orm.Model):
    _inherit = 'account.move'

    _columns = {
        'locked': fields.boolean('Locked', readonly=True),
    }

    def check_locked(self, cr, uid, ids, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            if move.locked:
                raise orm.except_orm(
                    _(u'Move Locked!'), move.name)

    def write(self, cr, uid, ids, vals, context=None):
        self.check_locked(cr=cr, uid=uid, ids=ids, context=context)
        return super(AccountMove, self).write(cr, uid,
                                              ids, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        self.check_locked(cr=cr, uid=uid, ids=ids, context=context)
        return super(AccountMove, self).unlink(cr, uid,
                                               ids, context=context)

    def button_cancel(self, cr, uid, ids, context=None):
        # Cancel a move was done directly in SQL
        # so we need to test manualy if the move is locked
        self.check_locked(cr=cr, uid=uid, ids=ids, context=context)
        return super(AccountMove, self).button_cancel(cr, uid,
                                                      ids, context=context)
