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
import psycopg2
import logging
from openerp.osv import orm

_logger = logging.getLogger(__name__)

def _format_inserts_values(vals):
    cols = vals.keys()
    if 'line_id' in cols:
        cols.remove('line_id')
    return (', '.join(cols), ', '.join(['%%(%s)s' % i for i in cols]))


class account_move(orm.Model):
    """redefine account move create to bypass orm
    if async_bypass_create is set to True in context"""

    _inherit = "account.move"

    def _prepare_line(self, cr, uid, move_id, line, vals, context=None):
        """Take incomming move line vals and complete line dict with
        missing data
        :param move_id: parent move id
        :param line: dict of vals of move line
        :param vals: dict of vals of move
        :returns: dict of val of move line completed
        """
        if isinstance(line, tuple):
            line = line[2]
        line['journal_id'] = vals.get('journal_id')
        line['date'] = vals.get('date')
        line['period_id'] = vals.get('period_id')
        line['company_id'] = vals.get('company_id')
        line['state'] = vals['state']
        line['move_id'] = move_id
        if line['debit'] and line['credit']:
            raise ValueError('debit and credit set on same line')
        if not line.get('analytic_account_id'):
            line['analytic_account_id'] = None
        for key in line:
            if line[key] is False:
                line[key] = None
        return line

    def _bypass_create(self, cr, uid, vals, context=None):
        """Create entries using cursor directly
        :returns: created id"""
        mvl_obj = self.pool['account.move.line']
        vals['company_id'] = context.get('company_id', False)
        vals['state'] = 'draft'
        if not vals.get('name'):
            vals['name'] = "/"
        sql = u"Insert INTO account_move (%s) VALUES (%s) RETURNING id"
        sql = sql % _format_inserts_values(vals)
        try:
            cr.execute(sql, vals)
        except psycopg2.Error as sql_exc:
            _logger.error('ORM by pass error for move: %s' % sql_exc.pgerror)
            raise
        created_id = cr.fetchone()[0]
        if vals.get('line_id'):
            for line in vals['line_id']:
                l_vals = self._prepare_line(cr, uid, created_id,
                                            line, vals, context=context)
                mvl_obj.create(cr, uid, l_vals, context=context)
        return created_id

    def create(self, cr, uid, vals, context=None):
        """Please refer to orm.BaseModel.create documentation"""
        if context is None:
            context = {}
        if context.get('async_bypass_create'):
            return self._bypass_create(cr, uid, vals, context=context)
        return super(account_move, self).create(cr, uid, vals, context=context)


class account_move_line(orm.Model):
    """redefine account move line create to bypass orm
    if async_bypass_create is set to True in context"""

    _inherit = "account.move.line"

    def create(self, cr, uid, vals, context=None):
        """Please refer to orm.BaseModel.create documentation"""
        if context is None:
            context = {}
        if context.get('async_bypass_create'):
                return self._bypass_create(cr, uid, vals, context=context)
        return super(account_move_line, self).create(cr, uid, vals, context=context)

    def _bypass_create(self, cr, uid, vals, context=None):
        """Create entries using cursor directly
        :returns: created id"""
        sql = u"Insert INTO account_move_line (%s) VALUES (%s) RETURNING id"
        sql = sql % _format_inserts_values(vals)
        try:
            cr.execute(sql, vals)
        except psycopg2.Error as sql_exc:
            _logger.error('ORM by pass error for move line: %s' % sql_exc.pgerror)
            raise
        return cr.fetchone()[0]
