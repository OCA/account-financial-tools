# -*- coding: utf-8 -*-
# © 2015-2016 Camptocamp SA (Vincent Renaville)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openerp import _, api, exceptions, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        result = super(AccountMove, self).create(vals)
        result.check_lock()
        return result

    @api.multi
    def write(self, vals):
        # check before and after modification
        self.check_lock()
        result = super(AccountMove, self).write(vals)
        self.check_lock()
        return result

    @api.multi
    def unlink(self):
        self.check_lock()
        return super(AccountMove, self).unlink()

    @api.multi
    def button_cancel(self):
        # Cancel a move was done directly in SQL
        # so we need to test manualy if the move is locked
        self.check_lock()
        return super(AccountMove, self).button_cancel()

    @api.multi
    def check_lock(self):
        date_range_obj = self.env['date.range']
        for move in self:
            current_ranges = date_range_obj.search(
                [('date_start', '<=', move.date),
                 ('date_end', '>=', move.date)])
            intersect = move.journal_id.locked_date_range_ids & current_ranges
            if intersect:
                error_msg = ""
                for range in intersect:
                    error_msg += (_('Date Range %s is locked!\n')
                                  % (range.name))
                raise exceptions.UserError(error_msg)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self, vals):
        result = super(AccountMoveLine, self).create(vals)
        result.check_lock()
        return result

    @api.multi
    def write(self, vals):
        # Allow to write "full_reconcile_id" on locked items;
        # this is so that items in locked date ranges can
        # still be fully reconciled.
        if len(vals) > 1 or 'full_reconcile_id' not in vals:
            # check before and after modification
            self.check_lock()
            result = super(AccountMoveLine, self).write(vals)
            result.check_lock()
            return result

    @api.multi
    def unlink(self):
        self.check_lock()
        return super(AccountMoveLine, self).unlink()

    @api.multi
    def check_lock(self):
        date_range_obj = self.env['date.range']
        for move in self:
            current_ranges = date_range_obj.search(
                [('date_start', '<=', move.date),
                 ('date_end', '>=', move.date)])
            intersect = move.journal_id.locked_date_range_ids & current_ranges
            if intersect:
                error_msg = ""
                for range in intersect:
                    error_msg += (_('Date Range %s is locked!\n')
                                  % (range.name))
                raise exceptions.UserError(error_msg)


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    locked_date_range_ids = fields.Many2many(
        'date.range',
        rel='account_date_range_lock_journal',
        string="Locked date ranges")

    @api.model
    def create(self, vals):
        # Add every locked date range to journal
        journal = super(AccountJournal, self).create(vals)
        date_ranges = self.env['date.range'].search(
            [('company_id', '=', self.company_id.id,),
             ('lock_state', '=', 'locked')])
        journal.locked_date_range_ids = date_ranges
        return journal
