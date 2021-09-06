# Copyright 2021 Akretion France (http://www.akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    sequence_id = fields.Many2one(
        "ir.sequence",
        string="Entry Sequence",
        copy=False,
        check_company=True,
        domain="[('company_id', '=', company_id)]",
        help="This sequence will be used to generate the journal entry number.",
    )
    refund_sequence = fields.Boolean(
        string="Dedicated Credit Note Sequence",
        default=True,
        help="If enabled, you will be able to setup a sequence dedicated for refunds.",
    )
    refund_sequence_id = fields.Many2one(
        "ir.sequence",
        string="Credit Note Entry Sequence",
        copy=False,
        check_company=True,
        domain="[('company_id', '=', company_id)]",
        help="This sequence will be used to generate the journal entry number for refunds.",
    )

    @api.constrains("refund_sequence_id", "sequence_id")
    def _check_journal_sequence(self):
        for journal in self:
            if (
                journal.refund_sequence_id
                and journal.sequence_id
                and journal.refund_sequence_id == journal.sequence_id
            ):
                raise ValidationError(
                    _(
                        "On journal '%s', the same sequence is used as "
                        "Entry Sequence and Credit Note Entry Sequence."
                    )
                    % journal.display_name
                )
            if journal.sequence_id and not journal.sequence_id.company_id:
                raise ValidationError(
                    _(
                        "The company is not set on sequence '%s' configured on "
                        "journal '%s'."
                    )
                    % (journal.sequence_id.display_name, journal.display_name)
                )
            if journal.refund_sequence_id and not journal.refund_sequence_id.company_id:
                raise ValidationError(
                    _(
                        "The company is not set on sequence '%s' configured as "
                        "credit note sequence of journal '%s'."
                    )
                    % (journal.refund_sequence_id.display_name, journal.display_name)
                )

    @api.model
    def create(self, vals):
        if not vals.get("sequence_id"):
            vals["sequence_id"] = self._create_sequence(vals).id
        if (
            vals.get("type") in ("sale", "purchase")
            and vals.get("refund_sequence")
            and not vals.get("refund_sequence_id")
        ):
            vals["refund_sequence_id"] = self._create_sequence(vals, refund=True).id
        return super().create(vals)

    @api.model
    def _prepare_sequence(self, vals, refund=False):
        code = vals.get("code") and vals["code"].upper() or ""
        prefix = "%s%s/%%(range_year)s/" % (refund and "R" or "", code)
        seq_vals = {
            "name": "%s%s"
            % (vals.get("name", _("Sequence")), refund and _("Refund") + " " or ""),
            "company_id": vals.get("company_id") or self.env.company.id,
            "implementation": "no_gap",
            "prefix": prefix,
            "padding": 4,
            "use_date_range": True,
        }
        return seq_vals

    @api.model
    def _create_sequence(self, vals, refund=False):
        seq_vals = self._prepare_sequence(vals, refund=refund)
        return self.env["ir.sequence"].sudo().create(seq_vals)
