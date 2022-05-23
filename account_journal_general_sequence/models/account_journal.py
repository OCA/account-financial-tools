# Copyright 2022 Moduon
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class AccountJournal(models.Model):
    _inherit = "account.journal"

    entry_number_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Account entry number sequence",
        default=lambda self: self._default_entry_number_sequence(),
        copy=False,
        help="Sequence used for account entry numbering.",
    )

    def _default_entry_number_sequence(self):
        """Get the default sequence for all journals."""
        result = self.env["ir.sequence"].search(
            [("code", "=", "account_journal_general_sequence.default")]
        )
        if result:
            return result
        _logger.info("Creating default sequence for account move numbers")
        result = self.env["ir.sequence"].create(
            {
                "name": _("Account entry default numbering"),
                "code": "account_journal_general_sequence.default",
                "implementation": "no_gap",
                "prefix": "%(range_year)s/",
                "padding": 10,
                "use_date_range": True,
            }
        )
        return result
