from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class CancelJournalEntries(models.TransientModel):
    _name = 'cancel.journal.entries'

    delete_after = fields.Boolean("Delete after cancel")

    @api.multi
    def cancel_journal_entries(self):
        """ cancel multiple journal entries from the tree view."""
        account_move_recs = self.env['account.move'].browse(
            self._context.get('active_ids'))
        journal_names = account_move_recs.mapped('journal_id').filtered(
            lambda journal: journal.update_posted is False).mapped('name')
        if journal_names:
            error_msg = """You must enable Allow Cancelling Entries\
            from Journals %s""" % ', '.join(journal_names)
            raise UserError(_(error_msg))
        account_move_recs.button_cancel()
        for record in self:
            if record.delete_after:
                account_move_recs.unlink()
        return True


class CancelJournalLineEntries(models.TransientModel):
    _name = 'cancel.journal.line.entries'

    delete_after = fields.Boolean("Delete after cancel")

    @api.multi
    def cancel_journal_entries(self):
        """ cancel multiple journal entries from the tree view."""
        account_move_line_recs = self.env['account.move.line'].browse(
            self._context.get('active_ids'))
        account_move_recs = account_move_line_recs.mapped('move_id')
        journal_names = account_move_recs.mapped('journal_id').filtered(
            lambda journal: journal.update_posted is False).mapped('name')
        if journal_names:
            error_msg = """You must enable Allow Cancelling Entries\
            from Journals %s""" % ', '.join(journal_names)
            raise UserError(_(error_msg))
        account_move_recs.button_cancel()
        for record in self:
            if record.delete_after:
                account_move_recs.unlink()
        return True
