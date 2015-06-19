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


class AccountPeriod(orm.Model):
    _inherit = 'account.period'
    _columns = {
        'journal_period_ids': fields.one2many('account.journal.period',
                                              'period_id', 'Journal states'),
    }

    def add_all_journals(self, cr, uid, ids, context=None):
        this = self.browse(cr, uid, ids, context=context)[0]
        journal_period_obj = self.pool.get('account.journal.period')
        journal_period_ids = journal_period_obj\
            .search(cr, uid, [('period_id', '=', this.id)], context=context)
        journal_list = []
        for journal_period in journal_period_obj.browse(cr,
                                                        uid,
                                                        journal_period_ids,
                                                        context=context):
            journal_list.append(journal_period.journal_id.id)
        journal_ids = self.pool.get('account.journal')\
            .search(cr, uid, [('id', 'not in', journal_list)], context=context)
        for journal_id in journal_ids:
            journal_period_obj.create(cr,
                                      uid,
                                      {'period_id': this.id,
                                       'journal_id': journal_id,
                                       'state': this.state})
