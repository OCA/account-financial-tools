# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import ValidationError, UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    journal_lock_date = fields.Date(
        name='Lock Date',
        help="Moves cannot be entered nor modified in this "
             "journal prior to the lock date, unless the user "
             "has the Adviser role.",
    )

    @api.model
    def _can_bypass_journal_lock_date(self):
        """ This method is meant to be overridden to provide
        finer control on who can bypass the lock date """
        return self.env.user.has_group('account.group_account_manager')
