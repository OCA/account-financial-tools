# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import _, api, exceptions, fields, models


class DateRange(models.Model):
    _inherit = "date.range"

    @api.depends('locked_journal_ids')
    def _get_lock_state(self):
        journal_obj = self.env['account.journal']
        for range in self:
            all_journals = journal_obj.search(
                [('company_id', '=', range.company_id.id)])
            if not range.locked_journal_ids:
                range.lock_state = 'unlocked'
            elif range.locked_journal_ids == all_journals:
                range.lock_state = 'locked'
            else:
                range.lock_state = 'partial'

    lock_state = fields.Selection(
        [('unlocked', 'Unlocked'),
         ('partial', 'Partially locked'),
         ('locked', 'Locked')],
        compute="_get_lock_state",
        readonly=True,
        store=True)
    locked_journal_ids = fields.Many2many(
        'account.journal',
        rel='account_date_range_lock_journal',
        string="Locked journals")

    @api.model
    def create(self, vals):
        # Check if fiscal year is locked; if so, add all journals
        # to set is as locked
        journal_obj = self.env['account.journal']
        if ('company_id' in vals and
                'date_start' in vals and 'date_end' in vals):
            fy_ranges = self.search(
                [('type_id.fiscal_year', '=', True),
                 ('lock_state', '=', 'locked'),
                 ('date_start', '<=', vals['date_start']),
                 ('date_end', '>=', vals['date_end'])])
            if fy_ranges:
                all_journal_ids = journal_obj.search(
                    [('company_id', '=', vals['company_id'])]).ids
                vals['locked_journal_ids'] = [(6, 0, all_journal_ids)]
        return super(DateRange, self).create(vals)

    @api.multi
    def write(self, vals):
        for range in self:
            if range.lock_state == 'locked':
                raise exceptions.UserError(
                    _("Cannot modify locked date range %s!")
                    % (range.name))
        return super(DateRange, self).write(vals)

    @api.multi
    def unlink(self):
        for range in self:
            if range.lock_state == 'locked':
                raise exceptions.UserError(
                    _("Cannot delete locked date range %s!")
                    % (range.name))
        return super(DateRange, self).unlink()
