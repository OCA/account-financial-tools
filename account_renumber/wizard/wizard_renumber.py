# Copyright 2009 Pexego Sistemas Informáticos. All Rights Reserved
# Copyright 2016 Jairo Llopis <jairo.llopis@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import date
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
        comodel_name='account.journal',
        relation='account_journal_wzd_renumber_rel',
        column1='wizard_id',
        column2='journal_id',
        string="Journals",
        required=True,
        help="Journals to renumber",
    )
    number_next = fields.Integer(
        string='First Number',
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

    @api.multi
    def renumber(self):
        """Renumber all the posted moves on the given journal and periods.

        :return dict:
            Window action to open the renumbered moves, to review them.
        """
        reset_sequences = self.env["ir.sequence"]
        reset_ranges = self.env["ir.sequence.date_range"]

        _logger.debug("Searching for account moves to renumber.")
        move_ids = self.env['account.move'].search(
            [('journal_id', 'in', self.journal_ids.ids),
             ('date', '>=', self.date_from),
             ('date', '<=', self.date_to),
             ('state', '=', 'posted')],
            order='date, id')
        if not move_ids:
            raise exceptions.MissingError(
                _('No records found for your selection!'))

        _logger.debug("Renumbering %d account moves.", len(move_ids))
        for move in move_ids:
            sequence = move.journal_id.sequence_id
            if sequence not in reset_sequences:
                if sequence.use_date_range:
                    date_range = self.env["ir.sequence.date_range"].search(
                        [("sequence_id", "=", sequence.id),
                         ("date_from", "<=", move.date),
                         ("date_to", ">=", move.date)]
                    )
                    if date_range and date_range not in reset_ranges:
                        date_range.sudo().number_next = self.number_next
                        reset_ranges |= date_range
                else:
                    sequence.sudo().number_next = self.number_next
                    reset_sequences |= sequence

            # Generate (using our own get_id) and write the new move number
            move.name = (sequence.with_context(ir_sequence_date=move.date)
                         .next_by_id())

        _logger.debug("%d account moves renumbered.", len(move_ids))

        return {
            'type': 'ir.actions.act_window',
            'name': _("Renumbered account moves"),
            'res_model': 'account.move',
            'domain': [("id", "in", move_ids.ids)],
            'view_type': 'form',
            'view_mode': 'tree',
            'context': self.env.context,
            'target': 'current',
        }
