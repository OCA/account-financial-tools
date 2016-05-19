# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import _, api, exceptions, fields, models


class DateRangeLock(models.TransientModel):
    _name = 'date.range.lock'

    date_range_id = fields.Many2one('date.range',
                                    string='Date Range',
                                    required=True)
    fy_range = fields.Boolean(related='date_range_id.type_id.fiscal_year',
                              readonly=True)
    journal_ids = fields.Many2many(
        'account.journal',
        rel='wizard_date_range_lock_journal',
        string='Journals')

    @api.onchange('date_range_id')
    def onchange_date_range(self):
        if self.date_range_id:
            return {
                'domain': {
                    'journal_ids': [
                        ('id',
                         'not in',
                         self.date_range_id.locked_journal_ids.ids)
                    ]
                }
            }

    @api.multi
    def lock(self):
        move_obj = self.env['account.move']
        journal_obj = self.env['account.journal']
        date_range_obj = self.env['date.range']
        for wizard in self:
            range = wizard.date_range_id
            all_journals = journal_obj.search(
                [('company_id', '=', range.company_id.id)])

            if range.type_id.fiscal_year or not wizard.journal_ids:
                # FY or no journals : full lock
                locked_journals = all_journals
            else:
                # Partial lock
                locked_journals = range.locked_journal_ids | wizard.journal_ids

            draft_move = move_obj.search(
                [('state', '=', 'draft'),
                 ('journal_id', 'in', locked_journals.ids),
                 ('date', '>=', range.date_start),
                 ('date', '<=', range.date_end)],
                order='date')
            if draft_move:
                raise exceptions.UserError(
                    _('Unposted move in selected date range, \
                    please post it before locking them'))

            range.locked_journal_ids = locked_journals

            if range.type_id.fiscal_year and range.lock_state == 'locked':
                # Lock all date ranges below this one
                child_ranges = date_range_obj.with_context(
                    active_test=False).search(
                    [('company_id', '=', range.company_id.id),
                     ('date_start', '>=', range.date_start),
                     ('date_end', '<=', range.date_end),
                     ('id', '!=', range.id)])
                for child in child_ranges:
                    child.locked_journal_ids = all_journals
