# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#   Author: Leonardo Pistone
#   Copyright 2014 Camptocamp SA
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################
"""Wizards for batch posting."""

from openerp.osv import fields, orm
from openerp.addons.connector.session import ConnectorSession
from openerp.addons.connector.queue.job import job


class AccountMoveMarker(orm.TransientModel):

    """Wizard to mark account moves for batch posting."""

    _name = "account.move.marker"
    _inherit = "account.common.report"
    _description = "Mark Journal Items for batch posting"

    _columns = {
        'action': fields.selection([
            ('mark', 'Mark for posting'),
            ('unmark', 'Unmark for posting'),
        ], "Action", required=True),
        'eta': fields.integer('Seconds to wait before starting the jobs')
    }

    _defaults = {
        'action': 'mark',
    }

    def button_mark(self, cr, uid, ids, context=None):
        """Create a single job that will create one job per move.

        Return action.

        """
        session = ConnectorSession(cr, uid, context=context)
        for wizard_id in ids:
            # to find out what _classic_write does, read the documentation.
            wizard_data = self.read(cr, uid, wizard_id, context=context,
                                    load='_classic_write')
            wizard_data.pop('id')
            process_wizard.delay(session, self._name, wizard_data)

        return {'type': 'ir.actions.act_window_close'}

    def process_wizard(self, cr, uid, ids, context=None):
        """Choose the correct list of moves to mark and then validate."""
        for wiz in self.browse(cr, uid, ids, context=context):

            move_obj = self.pool['account.move']

            domain = [('state', '=', 'draft')]

            if wiz.filter == 'filter_period':
                period_pool = self.pool['account.period']
                period_ids = period_pool.search(cr, uid, [
                    ('date_start', '>=', wiz.period_from.date_start),
                    ('date_stop', '<=', wiz.period_to.date_stop),
                ], context=context)

                domain.append((
                    'period_id',
                    'in',
                    period_ids
                ))
            elif wiz.filter == 'filter_date':
                domain += [
                    ('date', '>=', wiz.date_from),
                    ('date', '<=', wiz.date_to),
                ]

            if wiz.journal_ids:
                domain.append((
                    'journal_id',
                    'in',
                    [journal.id for journal in wiz.journal_ids]
                ))

            move_ids = move_obj.search(cr, uid, domain, context=context)

            if wiz.action == 'mark':
                move_obj.mark_for_posting(cr, uid, move_ids, eta=wiz.eta,
                                          context=context)

            elif wiz.action == 'unmark':
                move_obj.unmark_for_posting(cr, uid, move_ids, context=context)


@job
def process_wizard(session, model_name, wizard_data):
    """Create jobs to validate Journal Entries."""

    wiz_obj = session.pool[model_name]
    new_wiz_id = wiz_obj.create(
        session.cr,
        session.uid,
        wizard_data,
        session.context
    )

    wiz_obj.process_wizard(
        session.cr,
        session.uid,
        ids=[new_wiz_id],
        context=session.context,
    )
