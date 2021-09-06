# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_name(self):
        for move in self.filtered(
            lambda m: (m.name == "/" or not m.name)
            and m.state == "posted"
            and m.journal_id
            and m.journal_id.sequence_id
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
            move.name = seq.next_by_id(sequence_date=move.date)
        super()._compute_name()
        for move in self.filtered(
            lambda m: m.name and m.name != "/" and m.state != "posted"
        ):
            move.name = "/"
