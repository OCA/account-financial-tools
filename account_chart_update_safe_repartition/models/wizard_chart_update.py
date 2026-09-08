# Copyright 2026 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class WizardUpdateChartsAccounts(models.TransientModel):
    _inherit = "wizard.update.charts.accounts"

    update_tax_repartition_preserve_moves = fields.Boolean(
        string="Update tax repartition preserving posted moves",
        help=(
            "Apply chart template changes to tax repartition lines "
            "referenced by posted entries, without deleting them."
        ),
        default=False,
    )

    @api.model
    def diff_fields(self, record_values, real):
        result = super().diff_fields(record_values, real)
        if (
            not self.update_tax_repartition_preserve_moves
            or real._name != "account.tax"
            or "repartition_line_ids" not in record_values
            or "repartition_line_ids" not in self.tax_field_ids.mapped("name")
        ):
            return result
        rep_commands = self._diff_repartition_line_ids_preserve_moves(
            record_values["repartition_line_ids"], real
        )
        if rep_commands:
            result["repartition_line_ids"] = rep_commands
        else:
            result.pop("repartition_line_ids", None)
        return result

    def _repartition_line_key_from_vals(self, vals):
        return (
            vals.get("document_type"),
            vals.get("repartition_type"),
            vals.get("sequence", 0),
        )

    def _find_repartition_line_for_template(self, template_vals, tax):
        document_type = template_vals.get("document_type")
        repartition_type = template_vals.get("repartition_type")
        sequence = template_vals.get("sequence", 0)
        candidates = tax.repartition_line_ids.filtered(
            lambda line,
            document_type=document_type,
            repartition_type=repartition_type: (
                line.document_type == document_type
                and line.repartition_type == repartition_type
            )
        )
        if not candidates:
            return candidates
        exact = candidates.filtered(
            lambda line, sequence=sequence: line.sequence == sequence
        )
        if len(exact) == 1:
            return exact
        if len(candidates) == 1:
            return candidates
        return exact[:1]

    def _repartition_line_has_aml(self, rep_line):
        return bool(
            self.env["account.move.line"].search_count(
                [("tax_repartition_line_id", "=", rep_line.id)],
                limit=1,
            )
        )

    def _template_repartition_account_exists(self, vals):
        if "account_id" not in vals:
            return True
        account_xml_id = vals["account_id"]
        full_xml_id = (
            f"account.{self.company_id.id}_{account_xml_id}"
            if "." not in account_xml_id
            else account_xml_id
        )
        return bool(self.env.ref(full_xml_id, raise_if_not_found=False))

    def _append_wizard_log(self, message):
        _logger.info(message)
        if not self.log:
            self.log = message
        else:
            self.log += f"\n{message}"

    def _log_repartition_preserve_warning(self, tax, rep_line):
        msg = _(
            "Tax %(tax)s: keeping repartition line %(line)s "
            "(referenced by posted entries)."
        ) % {
            "tax": tax.display_name,
            "line": rep_line.id,
        }
        _logger.warning(msg)
        self._append_wizard_log(msg)

    def _diff_repartition_line_ids_preserve_moves(self, template_commands, tax):
        """Build o2m commands updating repartition lines in-place when referenced."""
        template_vals_list = [
            command[2]
            for command in template_commands
            if command[0] == 0 and command[1] == 0
        ]
        matched_existing_ids = set()
        commands = []

        for template_vals in template_vals_list:
            key = self._repartition_line_key_from_vals(template_vals)
            existing = self._find_repartition_line_for_template(template_vals, tax)
            if not existing:
                msg = _(
                    "Tax %(tax)s: template line %(key)s has no match; "
                    "skipped in preserve-moves mode."
                ) % {
                    "tax": tax.display_name,
                    "key": key,
                }
                _logger.info(msg)
                self._append_wizard_log(msg)
                continue
            existing = existing[0]
            matched_existing_ids.add(existing.id)
            line_diff = super().diff_fields(template_vals, existing)
            if not line_diff:
                continue
            if not self._template_repartition_account_exists(template_vals):
                line_diff.pop("account_id", None)
                if not line_diff:
                    continue
            commands.append((1, existing.id, line_diff))

        for existing in tax.repartition_line_ids:
            if existing.id in matched_existing_ids:
                continue
            if self._repartition_line_has_aml(existing):
                self._log_repartition_preserve_warning(tax, existing)
            else:
                msg = _(
                    "Tax %(tax)s: repartition line %(line)s has no template match; "
                    "kept in preserve-moves mode."
                ) % {
                    "tax": tax.display_name,
                    "line": existing.id,
                }
                _logger.info(msg)
                self._append_wizard_log(msg)

        return commands
