# Copyright 2021 Ecosoft Co., Ltd. (http://ecosoft.co.th)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    sequence_option = fields.Boolean(
        compute="_compute_name",
        default=False,
        copy=False,
        store=True,
        index=True,
    )

    @api.depends("posted_before", "state", "journal_id", "date")
    def _compute_name(self):
        options = self.env["ir.sequence.option.line"].get_model_options(self._name)
        move_to_update_name = self.filtered(
            lambda mv: mv.name not in (False, "/") and mv.state == "posted"
        )
        if not options or not move_to_update_name:
            return super()._compute_name()
        no_sequence_found = False
        for move in move_to_update_name:
            if not move.sequence_option:
                sequence = self.env["ir.sequence.option.line"].get_sequence(
                    move, options=options
                )
                if sequence:
                    move_name = sequence.next_by_id(sequence_date=move.date)
                    move.with_context(hash_version=1).update(
                        {
                            "name": move_name,
                            "sequence_option": True,
                            "payment_reference": move_name,
                        }
                    )

                else:
                    res = super()._compute_name()
                    no_sequence_found = True

        if no_sequence_found:
            return res

    # Bypass constrains if sequence is defined
    def _constrains_date_sequence(self):
        records = self.filtered(
            lambda l: self.env["ir.sequence.option.line"].get_sequence(l)
        )
        return super(AccountMove, self - records)._constrains_date_sequence()

    def _get_last_sequence_domain(self, relaxed=False):
        (where_string, param) = super()._get_last_sequence_domain(relaxed=relaxed)
        where_string += " AND coalesce(sequence_option, false) = false "
        return where_string, param
