# Copyright 2009 Pexego Sistemas Informáticos. All Rights Reserved
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date

from psycopg2 import DatabaseError

from odoo import _, api, exceptions, fields, models

_logger = logging.getLogger(__name__)


class WizardRenumber(models.TransientModel):
    _name = "wizard.renumber"
    _description = "Account renumber wizard"

    date_from = fields.Date(
        string="Starting date",
        required=True,
        default=lambda self: self._default_date_from(),
        help="Start renumbering in this date, inclusive.",
    )
    date_to = fields.Date(
        string="Finish date",
        required=True,
        default=lambda self: self._default_date_to(),
        help="Finish renumbering in this date, inclusive.",
    )
    journal_ids = fields.Many2many(
        comodel_name="account.journal",
        relation="account_journal_wzd_renumber_rel",
        column1="wizard_id",
        column2="journal_id",
        string="Journals",
        required=True,
        help="Journals to renumber",
    )
    number_next = fields.Integer(
        string="First Number",
        default=1,
        required=True,
        help="Journal sequences will start counting on this number",
    )

    @api.model
    def _default_date_from(self):
        """Day 1 of current year by default."""
        return date(self._default_date_to().year, 1, 1)

    @api.model
    def _default_date_to(self):
        """Today by default."""
        return fields.Date.from_string(fields.Date.context_today(self))

    def renumber(self):
        """Renumber all the posted moves on the given journal and periods.

        :return dict:
            Window action to open the renumbered moves, to review them.
        """
        sequence_mixin = self.env["sequence.mixin"]

        _logger.debug("Searching for account moves to renumber.")
        move_ids = self.env["account.move"].search(
            [
                ("journal_id", "in", self.journal_ids.ids),
                ("date", ">=", self.date_from),
                ("date", "<=", self.date_to),
                ("state", "=", "posted"),
            ],
            order="date, id",
        )
        if not move_ids:
            raise exceptions.MissingError(_("No records found for your selection!"))

        _logger.debug("Renumbering %d account moves.", len(move_ids))
        seq_num = self.number_next
        for move in move_ids:
            sequence = move._get_starting_sequence()
            format_string, format_values = sequence_mixin._get_sequence_format_param(
                sequence
            )
            format_values["seq"] = seq_num
            format_values["year"] = move[sequence_mixin._sequence_date_field].year % (
                10 ** format_values["year_length"]
            )
            format_values["month"] = move[sequence_mixin._sequence_date_field].month
            sequence = format_string.format(**format_values)
            try:
                move[sequence_mixin._sequence_field] = sequence
                move.flush_recordset([sequence_mixin._sequence_field])
            except DatabaseError as e:
                # 23P01 ExclusionViolation
                # 23505 UniqueViolation
                if e.pgcode not in ("23P01", "23505"):
                    raise e
            sequence_mixin._compute_split_sequence()
            move.flush_recordset(["sequence_prefix", "sequence_number"])
            seq_num += 1
        _logger.debug("%d account moves renumbered.", len(move_ids))

        return {
            "type": "ir.actions.act_window",
            "name": _("Renumbered account moves"),
            "res_model": "account.move",
            "domain": [("id", "in", move_ids.ids)],
            "view_mode": "tree",
            "context": self.env.context,
            "target": "current",
        }
