# -*- coding: utf-8 -*-
# © 2016 Camptocamp SA (Matthieu Dietrich)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import _, api, exceptions, fields, models


class DateRange(models.Model):
    _inherit = "date.range"

    @api.depends('locked_journal_ids')
    def _get_accounting_lock_state(self):
        journal_obj = self.env['account.journal']
        for range in self:
            range.accounting_lock_state = False
            # Only set state on ranges with accounting type
            if range.type_id.accounting:
                all_journals = journal_obj.search(
                    [('company_id', '=', range.company_id.id)])
                if not range.locked_journal_ids:
                    range.accounting_lock_state = 'unlocked'
                elif range.locked_journal_ids == all_journals:
                    range.accounting_lock_state = 'locked'
                else:
                    range.accounting_lock_state = 'partial'

    accounting_lock_state = fields.Selection(
        [('unlocked', 'Unlocked'),
         ('partial', 'Partially locked'),
         ('locked', 'Locked')],
        compute="_get_accounting_lock_state",
        readonly=True,
        store=True)
    locked_journal_ids = fields.Many2many(
        'account.journal',
        rel='account_date_range_lock_journal',
        string="Locked journals")

    @api.model
    def create(self, vals):
        # Check if account fiscal year is locked; if so, add all journals
        # to set is as locked
        journal_obj = self.env['account.journal']
        result = super(DateRange, self).create(vals)
        if result.type_id.accounting:
            # Only lock accounting periods
            fy_ranges = self.search(
                [('type_id.accounting', '=', True),
                 ('type_id.fiscal_year', '=', True),
                 ('accounting_lock_state', '=', 'locked'),
                 ('date_start', '<=', result.date_start),
                 ('date_end', '>=', result.date_end)])
            if fy_ranges:
                all_journals = journal_obj.search(
                    [('company_id', '=', result.company_id)])
                result.locked_journal_ids = all_journals
        return result

    @api.multi
    def write(self, vals):
        for range in self:
            # Allow to modify locked_journal_ids (otherwise, the
            # accounting range cannot be unlocked)
            if (range.type_id.accounting and
                    range.accounting_lock_state == 'locked' and
                    'locked_journal_ids' not in vals):
                raise exceptions.UserError(
                    _("Cannot modify locked date range %s!")
                    % (range.name))
        return super(DateRange, self).write(vals)

    @api.multi
    def unlink(self):
        for range in self:
            if (range.type_id.accounting and
                    range.accounting_lock_state == 'locked'):
                raise exceptions.UserError(
                    _("Cannot delete locked date range %s!")
                    % (range.name))
        return super(DateRange, self).unlink()
