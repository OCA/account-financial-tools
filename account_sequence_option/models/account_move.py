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
        #
        options = self.env["ir.sequence.option.line"].get_model_options(self._name)
        # On post, get the sequence option
        if options:
            for rec in self.filtered(
                lambda l: l.name in (False, "/") and l.state == "posted"
            ):
                sequence = self.env["ir.sequence.option.line"].get_sequence(
                    rec, options=options
                )
                if sequence:
                    rec.name = sequence.next_by_id(sequence_date=rec.date)
                    rec.sequence_option = True

        # Call super()
        super()._compute_name()
        if options:
            for rec in self:
                # On create new, odoo may suggest the 1st new number, remove it.
                if (
                    not rec.create_date
                    and rec.state == "draft"
                    and rec.name not in (False, "/")
                ):
                    rec.name = "/"
                # On cancel/draft w/o number assigned yet, ensure no odoo number assigned.
                if (
                    rec.create_date
                    and rec.state in ("draft", "cancel")
                    and rec.name not in (False, "/")
                    and not rec.sequence_option
                ):
                    rec.name = "/"

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
