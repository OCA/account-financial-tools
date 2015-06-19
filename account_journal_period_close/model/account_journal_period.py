# -*- coding: utf-8 -*-
#
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
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
#

from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountJournalPeriod(orm.Model):
    _inherit = 'account.journal.period'
    _order = "type,name"
    _columns = {
        'type': fields.related('journal_id', 'type', type='char',
                               relation='account.journal',
                               string='Journal Type',
                               store=True, readonly=True)
    }

    _sql_constraints = [
        ('journal_period_uniq', 'unique(period_id, journal_id)',
         'You can not add same journal in the same period twice.'),
    ]

    def _check(self, cr, uid, ids, context=None):
        return True

    def action_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'})

    def action_done(self, cr, uid, ids, context=None):
        for journal_period in self.browse(cr, uid, ids, context=context):
            draft_move_ids = self.pool.get('account.move')\
                .search(cr, uid, [('period_id', '=',
                                   journal_period.period_id.id),
                                  ('state', '=', "draft"),
                                  ('journal_id', '=',
                                   journal_period.journal_id.id)],
                        context=context)
            if draft_move_ids:
                raise orm.except_orm(_('Invalid Action!'),
                                     _('In order to close a journal,'
                                       ' you must first post related'
                                       ' journal entries.'))
        return self.write(cr, uid, ids, {'state': 'done'})

    def create(self, cr, uid, values, context=None):
        if 'name' not in values:
            if values.get('period_id') and values.get('journal_id'):
                journal = self.pool.get('account.journal')\
                    .browse(cr, uid, values['journal_id'], context=context)
                period = self.pool.get('account.period')\
                    .browse(cr, uid, values['period_id'], context=context)
                values.update({'name': (journal.code or journal.name)+':' +
                               (period.name or '')})
        return super(AccountJournalPeriod, self).create(cr,
                                                        uid,
                                                        values,
                                                        context=context)
