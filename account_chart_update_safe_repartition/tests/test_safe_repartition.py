# Copyright 2026 Binhex
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import fields
from odoo.tests import tagged

from odoo.addons.account_chart_update.tests.common import TestAccountChartUpdateCommon


@tagged("-at_install", "post_install")
class TestSafeRepartition(TestAccountChartUpdateCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.tax_data = cls.chart_template_data["account.tax"]
        cls.tax_xml_id = next(iter(cls.tax_data))
        cls.tax_template = cls.tax_data[cls.tax_xml_id]
        cls.tax = cls.env.ref(f"account.{cls.company.id}_{cls.tax_xml_id}")
        cls.repartition = cls.tax.repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
            and line.document_type == "invoice"
        )[:1]
        cls.account_data = cls.chart_template_data["account.account"]
        cls.account_xml_id = next(iter(cls.account_data))
        cls.account = cls.env.ref(f"account.{cls.company.id}_{cls.account_xml_id}")
        cls.other_account = cls.env["account.account"].create(
            {
                "name": "Other tax account (test)",
                "code": "9999999",
                "account_type": cls.account.account_type,
                "company_ids": [(6, 0, cls.company.ids)],
            }
        )
        cls.repartition.account_id = cls.other_account
        cls._create_posted_move_with_repartition(cls.repartition)

    @classmethod
    def _create_posted_move_with_repartition(cls, repartition):
        journal = cls.env["account.journal"].search(
            [("company_id", "=", cls.company.id), ("type", "=", "general")],
            limit=1,
        )
        counter_account = cls.env["account.account"].search(
            [
                ("company_ids", "in", cls.company.id),
                ("id", "!=", repartition.account_id.id),
            ],
            limit=1,
        )
        move = cls.env["account.move"].create(
            {
                "journal_id": journal.id,
                "date": fields.Date.today(),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "debit",
                            "account_id": counter_account.id,
                            "debit": 10.0,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "tax repartition",
                            "account_id": repartition.account_id.id,
                            "debit": 0.0,
                            "credit": 10.0,
                            "tax_repartition_line_id": repartition.id,
                        },
                    ),
                ],
            }
        )
        move.action_post()

    def _template_repartition_commands(self, account_xml_id=None):
        commands = []
        account_xml_id = (
            self.account_xml_id if account_xml_id is None else account_xml_id
        )
        for command in self.tax_template["repartition_line_ids"]:
            vals = dict(command[2])
            if (
                vals.get("repartition_type") == "tax"
                and vals.get("document_type") == "invoice"
            ):
                vals["account_id"] = account_xml_id
                # Keep template sequence aligned with the real line used in setUpClass.
                vals["sequence"] = self.repartition.sequence
            commands.append((0, 0, vals))
        return commands

    def _commands_from_existing_lines(
        self, exclude_ids=None, override_account_xml_id=None
    ):
        """Build template-like commands from current tax lines (except excluded)."""
        exclude_ids = set(exclude_ids or [])
        commands = []
        for line in self.tax.repartition_line_ids:
            if line.id in exclude_ids:
                continue
            vals = {
                "document_type": line.document_type,
                "repartition_type": line.repartition_type,
                "sequence": line.sequence,
                "factor_percent": line.factor_percent,
            }
            if (
                override_account_xml_id
                and line.id == self.repartition.id
                and line.repartition_type == "tax"
                and line.document_type == "invoice"
            ):
                vals["account_id"] = override_account_xml_id
            elif line.account_id:
                xmlids = line.account_id.get_external_id()
                full_xmlid = xmlids.get(line.account_id.id) or ""
                prefix = f"account.{self.company.id}_"
                vals["account_id"] = (
                    full_xmlid[len(prefix) :]
                    if full_xmlid.startswith(prefix)
                    else full_xmlid
                )
            commands.append((0, 0, vals))
        return commands

    def _wizard(self, preserve_moves):
        return self.wizard_obj.with_company(self.company).create(
            {
                **self.wizard_vals,
                "update_tax_repartition_preserve_moves": preserve_moves,
            }
        )

    def _enable_repartition_field(self, wizard):
        wizard.tax_field_ids = self.env["ir.model.fields"].search(
            [("model", "=", "account.tax"), ("name", "=", "repartition_line_ids")]
        )

    def _extra_invoice_tax_repartition(self, sequence, with_aml=False):
        """Create an extra invoice/tax repartition line not present in template."""
        line = self.env["account.tax.repartition.line"].create(
            {
                "tax_id": self.tax.id,
                "document_type": "invoice",
                "repartition_type": "tax",
                "sequence": sequence,
                "account_id": self.other_account.id,
                "factor_percent": 100.0,
            }
        )
        if with_aml:
            self._create_posted_move_with_repartition(line)
        return line

    def test_preserve_moves_diff_uses_inplace_update(self):
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._template_repartition_commands()
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        diff = wizard.diff_fields(template_values, self.tax)
        self.assertIn("repartition_line_ids", diff)
        commands = diff["repartition_line_ids"]
        self.assertFalse(any(command[0] == 5 for command in commands))
        update_commands = [command for command in commands if command[0] == 1]
        self.assertFalse(any(command[0] == 0 for command in commands))
        self.assertTrue(
            update_commands,
            "Expected in-place updates, not delete/recreate.",
        )
        updated_ids = {command[1] for command in update_commands}
        self.assertIn(self.repartition.id, updated_ids)

    def test_standard_mode_keeps_delete_and_recreate(self):
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._template_repartition_commands()
        wizard = self._wizard(preserve_moves=False)
        self._enable_repartition_field(wizard)
        diff = wizard.diff_fields(template_values, self.tax)
        self.assertIn("repartition_line_ids", diff)
        commands = diff["repartition_line_ids"]
        self.assertEqual(commands[0], (5, 0, 0))

    def test_preserve_moves_apply_keeps_repartition_id(self):
        repartition_id = self.repartition.id
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._template_repartition_commands()
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        wizard.write(
            {
                "update_tax": True,
                "update_account": False,
                "update_account_group": False,
                "update_tax_group": False,
                "update_fiscal_position": False,
            }
        )
        wizard.action_find_records()
        tax_wiz_lines = wizard.tax_ids.filtered(
            lambda line: line.update_tax_id == self.tax
        )
        self.assertEqual(len(tax_wiz_lines), 1)
        self.assertEqual(tax_wiz_lines.type, "updated")
        wizard._update_taxes({self.tax_xml_id: template_values})
        self.assertEqual(self.repartition.exists().id, repartition_id)

    def test_diff_fields_early_return_non_tax_model(self):
        """diff_fields skips repartition override when model is not account.tax."""
        wizard = self._wizard(preserve_moves=True)
        diff = wizard.diff_fields({"name": "test"}, self.env.company)
        self.assertNotIn("repartition_line_ids", diff)

    def test_diff_fields_early_return_no_repartition_field(self):
        """diff_fields returns immediately when repartition_line_ids is not selected."""
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._template_repartition_commands()
        wizard = self._wizard(preserve_moves=True)
        wizard.tax_field_ids = self.env["ir.model.fields"].search(
            [("model", "=", "account.tax"), ("name", "=", "name")]
        )
        diff = wizard.diff_fields(template_values, self.tax)
        self.assertNotIn("repartition_line_ids", diff)

    def test_diff_fields_pops_repartition_when_no_commands(self):
        """When preserve mode finds no line diffs, repartition_line_ids is removed."""
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._commands_from_existing_lines()
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        diff = wizard.diff_fields(template_values, self.tax)
        self.assertNotIn("repartition_line_ids", diff)

    def test_find_repartition_line_no_candidates(self):
        """_find_repartition_line_for_template returns empty with wrong type."""
        wizard = self._wizard(preserve_moves=True)
        result = wizard._find_repartition_line_for_template(
            {"document_type": "nonexistent", "repartition_type": "tax", "sequence": 0},
            self.tax,
        )
        self.assertFalse(result)

    def test_find_repartition_line_exact_among_multiple(self):
        """Exact sequence match wins when several candidates share type."""
        extra = self._extra_invoice_tax_repartition(
            sequence=self.repartition.sequence + 880
        )
        wizard = self._wizard(preserve_moves=True)
        result = wizard._find_repartition_line_for_template(
            {
                "document_type": "invoice",
                "repartition_type": "tax",
                "sequence": extra.sequence,
            },
            self.tax,
        )
        self.assertEqual(result, extra)

    def test_find_repartition_line_single_candidate_fallback(self):
        """With a single candidate, sequence mismatch still returns that line."""
        refund_tax_lines = self.tax.repartition_line_ids.filtered(
            lambda line: line.document_type == "refund"
            and line.repartition_type == "tax"
        )
        self.assertEqual(len(refund_tax_lines), 1)
        wizard = self._wizard(preserve_moves=True)
        result = wizard._find_repartition_line_for_template(
            {
                "document_type": "refund",
                "repartition_type": "tax",
                "sequence": refund_tax_lines.sequence + 50,
            },
            self.tax,
        )
        self.assertEqual(result, refund_tax_lines)

    def test_find_repartition_line_ambiguous_no_exact(self):
        """Multiple candidates without exact sequence yield an empty recordset."""
        self._extra_invoice_tax_repartition(sequence=self.repartition.sequence + 881)
        invoice_tax_lines = self.tax.repartition_line_ids.filtered(
            lambda line: line.document_type == "invoice"
            and line.repartition_type == "tax"
        )
        self.assertGreater(len(invoice_tax_lines), 1)
        wizard = self._wizard(preserve_moves=True)
        result = wizard._find_repartition_line_for_template(
            {
                "document_type": "invoice",
                "repartition_type": "tax",
                "sequence": self.repartition.sequence + 999999,
            },
            self.tax,
        )
        self.assertFalse(result)

    def test_unmatched_template_line_skipped(self):
        """Template line without matching existing rep line is skipped."""
        template_values = dict(self.tax_template)
        commands = self._template_repartition_commands()
        # Force no candidates (not merely sequence mismatch with a single fallback).
        commands.append(
            (
                0,
                0,
                {
                    "document_type": "nonexistent",
                    "repartition_type": "tax",
                    "sequence": 999,
                    "account_id": self.account_xml_id,
                },
            )
        )
        template_values["repartition_line_ids"] = commands
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        diff = wizard.diff_fields(template_values, self.tax)
        self.assertTrue(wizard.log)
        self.assertIn("no match", wizard.log)
        if "repartition_line_ids" in diff:
            create_commands = [c for c in diff["repartition_line_ids"] if c[0] == 0]
            self.assertFalse(create_commands)

    def test_unmatched_existing_line_without_aml_is_kept(self):
        """Existing rep line without AML and no template match is kept (not deleted)."""
        extra = self._extra_invoice_tax_repartition(
            sequence=self.repartition.sequence + 882, with_aml=False
        )
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._commands_from_existing_lines(
            exclude_ids=[extra.id],
            override_account_xml_id=self.account_xml_id,
        )
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        diff = wizard.diff_fields(template_values, self.tax)
        self.assertTrue(wizard.log)
        self.assertIn("no template match", wizard.log)
        self.assertIn(str(extra.id), wizard.log)
        if "repartition_line_ids" in diff:
            self.assertFalse(any(cmd[0] == 5 for cmd in diff["repartition_line_ids"]))

    def test_unmatched_existing_line_with_aml_logs_warning(self):
        """Existing unmatched line referenced by AML logs a preserve warning."""
        extra = self._extra_invoice_tax_repartition(
            sequence=self.repartition.sequence + 883, with_aml=True
        )
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._commands_from_existing_lines(
            exclude_ids=[extra.id],
            override_account_xml_id=self.account_xml_id,
        )
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        wizard.diff_fields(template_values, self.tax)
        self.assertTrue(wizard.log)
        self.assertIn("referenced by posted entries", wizard.log)
        self.assertIn(str(extra.id), wizard.log)

    def test_template_missing_account_skips_account_update(self):
        """Missing template account drops account_id from the in-place update."""
        template_values = dict(self.tax_template)
        template_values["repartition_line_ids"] = self._template_repartition_commands(
            account_xml_id="account_that_does_not_exist_xyz"
        )
        wizard = self._wizard(preserve_moves=True)
        self._enable_repartition_field(wizard)
        diff = wizard.diff_fields(template_values, self.tax)
        if "repartition_line_ids" in diff:
            for command in diff["repartition_line_ids"]:
                if command[0] == 1 and command[1] == self.repartition.id:
                    self.assertNotIn("account_id", command[2])

    def test_template_repartition_account_exists_without_account_key(self):
        wizard = self._wizard(preserve_moves=True)
        self.assertTrue(
            wizard._template_repartition_account_exists({"factor_percent": 100})
        )

    def test_append_wizard_log_appends_second_message(self):
        wizard = self._wizard(preserve_moves=True)
        wizard._append_wizard_log("first")
        wizard._append_wizard_log("second")
        self.assertEqual(wizard.log, "first\nsecond")

    def test_repartition_line_has_aml(self):
        wizard = self._wizard(preserve_moves=True)
        self.assertTrue(wizard._repartition_line_has_aml(self.repartition))
        orphan = self._extra_invoice_tax_repartition(
            sequence=self.repartition.sequence + 884, with_aml=False
        )
        self.assertFalse(wizard._repartition_line_has_aml(orphan))
