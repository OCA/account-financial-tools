# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    name = fields.Char(compute="_compute_name_by_sequence")
    # highest_name, sequence_prefix and sequence_number are not needed any more
    # -> compute=False to improve perf
    highest_name = fields.Char(compute=False)
    sequence_prefix = fields.Char(compute=False)
    sequence_number = fields.Integer(compute=False)

    @api.constrains('name', 'state')
    def _check_name_state_diagonal(self):
        for move in self:
            if move.state == 'posted' and move.name in ['', '/']:
                raise UserError('A move can not be posted with name "/" or empty value\n'
            "Check the journal sequence, please",)

    @api.depends("state", "journal_id", "date")
    def _compute_name_by_sequence(self):
        for move in self:
            name = move.name or "/"
            # I can't use posted_before in this IF because
            # posted_before is set to True in _post() at the same
            # time as state is set to "posted"
            if (
                move.state == "posted"
                and (not move.name or move.name == "/")
                and move.journal_id
                and move.journal_id.sequence_id
            ):
                if (
                    move.move_type in ("out_refund", "in_refund")
                    and move.journal_id.type in ("sale", "purchase")
                    and move.journal_id.refund_sequence
                    and move.journal_id.refund_sequence_id
                ):
                    seq = move.journal_id.refund_sequence_id
                else:
                    seq = move.journal_id.sequence_id
                # next_by_id(date) only applies on ir.sequence.date_range selection
                # => we use with_context(ir_sequence_date=date).next_by_id()
                # which applies on ir.sequence.date_range selection AND prefix
                name = seq.with_context(ir_sequence_date=move.date).next_by_id()
            move.name = name

    # We must by-pass this constraint of sequence.mixin
    def _constrains_date_sequence(self):
        return True

    def _post(self, soft=True):
        self.flush()
        return super()._post(soft=soft)

    def _compute_name(self):
        """Overwrite account module method in order to
        avoid side effect if legacy code call it directly
        like when creating entry from email.
        """
        return self._compute_name_by_sequence()
