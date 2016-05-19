# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import _, api, exceptions, fields, models


class DateRangeUnlock(models.TransientModel):
    _name = 'date.range.unlock'

    date_range_id = fields.Many2one(
        'date.range',
        string='Date Range',
        required=True,
        domain=[('type_id.fiscal_year', '=', False)])

    journal_ids = fields.Many2many(
        'account.journal',
        rel='wizard_date_range_unlock_journal',
        string='Journals')

    @api.onchange('date_range_id')
    def onchange_date_range(self):
        if self.date_range_id:
            return {
                'domain': {
                    'journal_ids': [
                        ('id',
                         'in',
                         self.date_range_id.locked_journal_ids.ids)
                    ]
                }
            }

    @api.multi
    def unlock(self):
        date_range_obj = self.env['date.range']
        for wizard in self:
            range = self.date_range_id
            # If range is inside a locked fiscal year, raise an error
            fy_ranges = date_range_obj.search(
                [('type_id.fiscal_year', '=', True),
                 ('lock_state', '=', 'locked'),
                 ('date_start', '<=', range.date_start),
                 ('date_end', '>=', range.date_end)])
            if fy_ranges:
                raise exceptions.UserError(
                    _('Date range %s is inside a locked fiscal year!')
                    % (range.name))
            if not self.journal_ids:
                range.locked_journal_ids = False
            else:
                range.locked_journal_ids -= self.journal_ids
