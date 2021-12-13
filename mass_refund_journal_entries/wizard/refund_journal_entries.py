from odoo import api, models, fields, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class RefundJournalEntries(models.TransientModel):
    _name = 'refund.journal.entries'

    type = fields.Boolean('Inverse', help='If checked the records is mark as normal otherwise as refund')

    @api.multi
    def refund_journal_entries(self):
        for record in self:
            """ refund multiple journal entries from the tree view."""
            account_move_recs = self.env['account.move'].browse(
                self._context.get('active_ids'))
            for move in account_move_recs:
                for line in move.line_ids:
                    if not line.invoice_id:
                        if record.type:
                            line.tax_sign = 1
                        else:
                            line.tax_sign = -1
                        _logger.info("MARK %s" % line.tax_sign)
        return True


class RefundJournalLineEntries(models.TransientModel):
    _name = 'refund.journal.line.entries'

    type = fields.Boolean('Inverse', help='If checked the records is mark as normal otherwise as refund')

    @api.multi
    def refund_journal_entries(self):
        for record in self:
            """ refund multiple journal entries from the tree view."""
            account_move_line_recs = self.env['account.move.line'].browse(
                self._context.get('active_ids'))
            account_move_recs = account_move_line_recs.mapped('move_id')
            for move in account_move_recs:
                for line in move.line_ids:
                    if not line.invoice_id:
                        if record.type:
                            line.tax_sign = 1
                        else:
                            line.tax_sign = -1
                        _logger.info("MARK %s" % line.tax_sign)
        return True
