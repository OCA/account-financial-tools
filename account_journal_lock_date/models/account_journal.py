# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class AccountJournal(models.Model):

    _inherit = 'account.journal'

    journal_lock_date_period_offset = fields.Integer(
        string="Lock date offset", default=0,
        help="Set a stricter (later) lock date for this journal with this "
             "offest in days respective of the period lock date."
    )
    has_period_lock_date = fields.Boolean(compute='_compute_lock_date')
    journal_lock_date = fields.Date(
        string="Lock date", readonly=True, store=True,
        compute='_compute_lock_date',
        help="Moves cannot be entered nor modified in this "
             "journal prior to the lock date, unless the user "
             "has the Adviser role."
    )

    @api.onchange('journal_lock_date_period_offset')
    def _onchange_lock_date_offset(self):
        if self.journal_lock_date_period_offset < 0:
            return {
                "warning": {
                    "title": "Negative lock date offset",
                    "message": "Offset must be positive: you can only set "
                               "stricter lock dates than the period lock date."
                },
                "value": {"journal_lock_date_period_offset":
                    abs(self.journal_lock_date_period_offset)}
            }

    @api.depends('journal_lock_date_period_offset', 'company_id.period_lock_date')
    def _compute_lock_date(self):
        for journal in self.filtered('company_id.period_lock_date'):
            period_lock_date = journal.company_id.period_lock_date
            offset = relativedelta(days=+journal.journal_lock_date_period_offset)
            journal.journal_lock_date = period_lock_date + offset
            journal.has_period_lock_date = True

    @api.model
    def _can_bypass_journal_lock_date(self):
        """ This method is meant to be overridden to provide
        finer control on who can bypass the lock date """
        return self.env.user.has_group('account.group_account_manager')
