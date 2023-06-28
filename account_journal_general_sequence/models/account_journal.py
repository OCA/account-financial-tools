# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    entry_number_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Account entry number sequence",
        compute="_compute_entry_number_sequence",
        domain="[('company_id', '=', company_id)]",
        check_company=True,
        readonly=False,
        store=True,
        copy=False,
        help="Sequence used for account entry numbering.",
    )
    entry_number_sequence_id_name = fields.Char(related="entry_number_sequence_id.code")

    @api.depends("company_id")
    def _compute_entry_number_sequence(self):
        """Get the default sequence for all journals."""
        for one in self:
            sequence = self.env["ir.sequence"].search(
                [
                    ("code", "=", "account_journal_general_sequence.default"),
                    ("company_id", "=", one.company_id.id),
                ]
            )
            if not sequence:
                _logger.info("Creating default sequence for account move numbers")
                sequence = self.env["ir.sequence"].create(
                    {
                        "name": _(
                            "Account entry default numbering (%s)",
                            one.company_id.name,
                        ),
                        "code": "account_journal_general_sequence.default",
                        "company_id": one.company_id.id,
                        "implementation": "no_gap",
                        "prefix": "%(range_year)s/",
                        "padding": 8,
                        "use_date_range": True,
                    }
                )
            one.entry_number_sequence_id = sequence
