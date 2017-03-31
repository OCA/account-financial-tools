# -*- coding: utf-8 -*-
# Copyright 2017 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _

from ..exceptions import JournalLockDateError


class AccountMove(models.Model):

    _inherit = 'account.move'

    @api.multi
    def _check_lock_date(self):
        res = super(AccountMove, self)._check_lock_date()
        if self.env['account.journal']._can_bypass_journal_lock_date():
            return res
        for move in self:
            lock_date = move.journal_id.journal_lock_date
            if lock_date and move.date <= lock_date:
                raise JournalLockDateError(
                    _("You cannot add/modify entries prior to and "
                      "inclusive of the journal lock date %s") %
                    (lock_date, ))
        return res
