# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import Command
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account_chart_update.tests.common import TestAccountChartUpdateCommon

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class TestAccountChartUpdate(TestAccountChartUpdateCommon):
    def _get_record_for_xml_id(self, xml_id):
        # To read company-dependent fields correctly
        return self.env.ref(f"account.{self.company.id}_{xml_id}").with_company(
            self.company
        )

    @mute_logger("odoo.models.unlink")
    def test_01_chart_update(self):
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        # Test ir.model.fields _compute_display_name
        field = wizard.fp_field_ids[:1]
        name = field.with_context(account_chart_update=True).display_name
        expected_name = f"{field.field_description} ({field.name})"
        self.assertEqual(name, expected_name)
        self.assertNotEqual(field.display_name, expected_name)
        # Test no changes
        self.assertEqual(wizard.state, "ready")
        self.assertFalse(wizard.tax_group_ids)
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        self.assertFalse(wizard.fiscal_position_ids)
        wizard.unlink()
        # Check that no action is performed if the option is not selected
        wizard_vals = self.wizard_vals.copy()
        wizard_vals.update(
            {
                "update_tax_group": False,
                "update_tax": False,
                "update_account": False,
                "update_fiscal_position": False,
            }
        )
        wizard = self.wizard_obj.with_company(self.company).create(wizard_vals)
        wizard.action_find_records()
        self.assertFalse(wizard.tax_group_ids)
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        self.assertFalse(wizard.fiscal_position_ids)
        # We delete the existing records so that they appear "to be created".
        domain = [("company_id", "=", self.company.id)]
        domain_account = [("company_ids", "in", self.company.ids)]
        # Before deleting taxes, delete the references in the models.
        self.env.cr.execute("DELETE FROM account_reconcile_model_line_account_tax_rel")
        self.env["account.tax"].search(domain).unlink()
        journals = self.env["account.journal"].search(domain)
        IrDefault = self.env["ir.default"]
        IrDefault.discard_records(journals)
        journals.unlink()
        accounts = self.env["account.account"].search(domain_account)
        IrDefault.discard_records(accounts)
        accounts.unlink()
        self.env["account.fiscal.position"].search(domain).unlink()
        self.env["account.group"].search(domain).unlink()
        wizard.unlink()
        # Now do the real one for detecting additions
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        # account.tax data
        tax_data = self.chart_template_data["account.tax"]
        tax_data_key_0 = list(tax_data)[0]
        tax_data_0 = tax_data[tax_data_key_0]
        self.assertEqual(len(wizard.tax_ids), len(tax_data))
        tax_types = wizard.tax_ids.mapped("type")
        self.assertIn("new", tax_types)
        self.assertNotIn("updated", tax_types)
        self.assertNotIn("deleted", tax_types)
        self.assertEqual(wizard.tax_ids.mapped("xml_id"), list(tax_data.keys()))
        # account.account data
        account_data = self.chart_template_data["account.account"]
        account_data_key_0 = list(account_data)[0]
        account_data_0 = account_data[account_data_key_0]
        self.assertEqual(len(wizard.account_ids), len(account_data))
        account_types = wizard.account_ids.mapped("type")
        self.assertIn("new", account_types)
        self.assertNotIn("updated", account_types)
        self.assertNotIn("deleted", account_types)
        self.assertEqual(wizard.account_ids.mapped("xml_id"), list(account_data.keys()))
        # account.group data
        account_group_data = self.chart_template_data["account.group"]
        self.assertEqual(len(wizard.account_group_ids), len(account_group_data))
        account_group_types = wizard.account_group_ids.mapped("type")
        # generic_coa has no account.group data
        self.assertNotIn("new", account_group_types)
        self.assertNotIn("updated", account_group_types)
        self.assertEqual(
            wizard.account_group_ids.mapped("xml_id"), list(account_group_data.keys())
        )
        # fiscal.position
        fp_data = self.chart_template_data["account.fiscal.position"]
        self.assertEqual(len(wizard.fiscal_position_ids), len(fp_data))
        fp_types = wizard.fiscal_position_ids.mapped("type")
        self.assertIn("new", fp_types)
        self.assertNotIn("updated", fp_types)
        self.assertNotIn("deleted", fp_types)
        wizard.action_update_records()
        self.assertEqual(wizard.state, "done")
        self.assertEqual(wizard.new_taxes, len(tax_data))
        self.assertEqual(wizard.new_accounts, len(account_data))
        self.assertEqual(wizard.new_fps, len(fp_data))
        self.assertTrue(wizard.log)
        # Search new records: tax + account
        new_tax = self._get_record_for_xml_id(tax_data_key_0)
        self.assertTrue(new_tax)
        new_account = self._get_record_for_xml_id(account_data_key_0)
        self.assertEqual(len(new_account.code), wizard.code_digits)
        self.assertTrue(new_account)
        wizard.unlink()
        # Update objects
        new_account.name = "Account name (updated)"
        new_tax.name = "Tax name (updated)"
        new_tax_group = self.env["account.tax.group"].create(
            {"name": "Test 1", "country_id": new_tax.country_id.id}
        )
        new_tax.tax_group_id = new_tax_group
        repartition = new_tax.repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        )[0]
        repartition.account_id = new_account.id
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.tax_field_ids += self.env["ir.model.fields"].search(
            [("model", "=", "account.tax"), ("name", "=", "repartition_line_ids")]
        )
        wizard.action_find_records()
        self.assertEqual(len(wizard.tax_ids), 1)
        self.assertEqual(wizard.tax_ids.type, "updated")
        self.assertEqual(wizard.tax_ids.update_tax_id, new_tax)
        self.assertEqual(len(wizard.account_ids), 1)
        self.assertEqual(wizard.account_ids.type, "updated")
        self.assertEqual(wizard.account_ids.update_account_id, new_account)
        wizard.action_update_records()
        self.assertEqual(wizard.updated_taxes, 1)
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(new_tax.name, tax_data_0["name"])
        self.assertNotEqual(new_tax.tax_group_id, new_tax_group)
        repartition = new_tax.repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        )
        self.assertNotEqual(repartition.account_id, new_account)
        self.assertEqual(new_account.name, account_data_0["name"])
        wizard.unlink()
        # Exclude fields from check
        new_tax.description = "Test description 2"
        new_account.name = "Other name 2"
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        wizard.tax_field_ids -= self.env["ir.model.fields"].search(
            [("model", "=", "account.tax"), ("name", "=", "description")]
        )
        wizard.account_field_ids -= self.env["ir.model.fields"].search(
            [("model", "=", "account.account"), ("name", "=", "name")]
        )
        wizard.action_find_records()
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        wizard.unlink()

    @mute_logger("odoo.models.unlink")
    def test_02_chart_update(self):
        # Test XML-ID matching + recreate
        # account.tax data
        tax_data = self.chart_template_data["account.tax"]
        tax_data_key_0 = list(tax_data)[0]
        tax_data_0 = tax_data[tax_data_key_0]
        # account.account data
        account_data = self.chart_template_data["account.account"]
        account_data_key_0 = list(account_data)[0]
        account_data_0 = account_data[account_data_key_0]
        new_tax = self._get_record_for_xml_id(tax_data_key_0)
        new_tax.name = "Test 1 tax name changed"
        new_account = self._get_record_for_xml_id(account_data_key_0)
        new_account.code = "200000"
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.tax_ids.update_tax_id, new_tax)
        self.assertEqual(wizard.tax_ids.type, "updated")
        self.assertEqual(wizard.account_ids.update_account_id, new_account)
        self.assertEqual(wizard.account_ids.type, "updated")
        wizard.action_update_records()
        self.assertEqual(wizard.updated_taxes, 1)
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(wizard.new_account_groups, 0)
        self.assertEqual(wizard.updated_account_groups, 0)
        self.assertEqual(wizard.updated_fps, 0)
        self.assertEqual(wizard.deleted_taxes, 0)
        self.assertEqual(new_tax.name, tax_data_0["name"])
        self.assertEqual(new_account.code, wizard.padded_code(account_data_0["code"]))
        # Test match by another field, there is no match by XML-ID
        self._get_model_data(new_tax).unlink()
        self._get_model_data(new_account).unlink()
        new_account.name = "Test 2 account name changed"
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.tax_ids.update_tax_id, new_tax)
        self.assertEqual(wizard.tax_ids.type, "updated")
        self.assertEqual(wizard.account_ids.update_account_id, new_account)
        self.assertEqual(wizard.account_ids.type, "updated")
        wizard.action_update_records()
        self.assertEqual(wizard.updated_taxes, 1)
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(new_tax.name, tax_data_0["name"])
        self.assertEqual(new_account.name, account_data_0["name"])
        wizard.unlink()
        # Test match by name, there is no match by XML-ID or by code
        self._get_model_data(new_account).unlink()
        new_account.code = "300000"
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.account_ids[0].update_account_id, new_account)
        self.assertEqual(wizard.account_ids[0].type, "updated")
        wizard.action_update_records()
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(new_account.code, wizard.padded_code(account_data_0["code"]))
        wizard.unlink()

    def test_03_diff_fields_ignores_whitespace_only_difference(self):
        """Trailing/leading spaces in translatable fields should not trigger a diff.

        Regression test: the wizard was stripping whitespace from the template
        value but not from the database value, causing false positives when
        the stored value had surrounding spaces (e.g. loaded from the chart
        template originally).
        """
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        account_data = self.chart_template_data["account.account"]
        account_xml_id = list(account_data)[0]
        account = self._get_record_for_xml_id(account_xml_id)
        original_name = account.name
        # Simulate a stored value with trailing/leading spaces
        account.with_context(lang="en_US").name = f"  {original_name}  "
        # Template values also carry the same surrounding spaces
        record_values = {"name": f"  {original_name}  "}
        result = wizard.diff_fields(record_values, account)
        self.assertNotIn(
            "name",
            result,
            "Whitespace-only difference in translatable field should not be a diff",
        )

    def test_04_account_group_code_prefix_end_no_false_positive(self):
        """Account group with code_prefix_end > code_prefix_start should not be flagged.

        Regression test: the wizard's condition for resolving the expected
        code_prefix_end was inverted — it used the template's end value only
        when end < start (i.e. the invalid case) and fell back to start
        otherwise, producing a false diff whenever the group had a genuine
        range like 643-648.
        """
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # Simulate template data for an account group with a range (start != end)
        t_data = {
            "test_group_range": {
                "name": "Test Range Group",
                "code_prefix_start": "643",
                "code_prefix_end": "648",
            },
        }
        # Create the real account group in the database with the same range
        group = self.env["account.group"].create(
            {
                "name": "Test Range Group",
                "code_prefix_start": "643",
                "code_prefix_end": "648",
                "company_id": self.company.id,
            }
        )
        # Register the xmlid so _find_record_matching can locate it
        self.env["ir.model.data"].create(
            {
                "name": f"{self.company.id}_test_group_range",
                "module": "account",
                "model": "account.group",
                "res_id": group.id,
            }
        )
        wizard._find_account_groups(t_data)
        updated = wizard.account_group_ids.filtered(lambda r: r.type == "updated")
        self.assertFalse(
            updated,
            "Account group with matching code_prefix_end "
            "should not be flagged as updated",
        )

    def test_05_installed_charts(self):
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        chart_template_installed = wizard._chart_template_selection()
        all_chart_templates = self.env[
            "account.chart.template"
        ]._get_chart_template_mapping()
        only_installed = list(
            filter(lambda x: x["installed"], all_chart_templates.values())
        )
        self.assertEqual(len(chart_template_installed), len(only_installed))

    @mute_logger("odoo.models.unlink")
    def test_06_fiscal_position_ids_and_original_tax_ids(self):
        """Wizard must diff and update the new account.tax M2M fields that
        replaced the removed account.fiscal.position.tax model.
        """
        # sale_export_tax_template carries both fiscal_position_ids and
        # original_tax_ids in the generic_coa template.
        tax = self._get_record_for_xml_id("sale_export_tax_template")
        expected_fp_ids = set(tax.fiscal_position_ids.ids)
        expected_original_ids = set(tax.original_tax_ids.ids)
        self.assertTrue(expected_fp_ids)
        self.assertTrue(expected_original_ids)
        # No drift: wizard should not flag the tax as updated.
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        self.assertFalse(
            wizard.tax_ids.filtered(lambda r: r.update_tax_id == tax),
            "Tax matching the template should not be flagged as updated",
        )
        wizard.unlink()
        # Introduce drift on both fields and check detection + restoration.
        tax.fiscal_position_ids = [Command.clear()]
        tax.original_tax_ids = [Command.clear()]
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        wizard.action_find_records()
        wiz_tax = wizard.tax_ids.filtered(lambda r: r.update_tax_id == tax)
        self.assertEqual(wiz_tax.type, "updated")
        wizard.action_update_records()
        tax.invalidate_recordset()
        self.assertEqual(set(tax.fiscal_position_ids.ids), expected_fp_ids)
        self.assertEqual(set(tax.original_tax_ids.ids), expected_original_ids)

    def test_07_many2many_string_diff_is_order_independent(self):
        """Same records in a different order must not be reported as a diff."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax = self._get_record_for_xml_id("sale_export_tax_template")
        # Add a second fiscal position so we can test ordering.
        extra_fp = self._get_record_for_xml_id(
            "template_generic_domestic_fiscal_position"
        )
        tax.fiscal_position_ids = [
            Command.set((tax.fiscal_position_ids | extra_fp).ids)
        ]
        fp_short_xmlids = [
            fp.get_external_id()[fp.id].split("_", maxsplit=1)[1]
            for fp in tax.fiscal_position_ids
        ]
        self.assertGreater(len(fp_short_xmlids), 1)
        reversed_value = ",".join(reversed(fp_short_xmlids))
        result = wizard.diff_fields({"fiscal_position_ids": reversed_value}, tax)
        self.assertNotIn(
            "fiscal_position_ids",
            result,
            "Reordered m2m values must not be flagged as a diff",
        )

    def test_08_tag_ids_post_loop_drift(self):
        """Template drops empty cells — tag drift on an account must still
        be detected via the synthetic post-loop and result in a cleared
        tag_ids after update.
        """
        account = self._get_record_for_xml_id(
            list(self.chart_template_data["account.account"])[0]
        )
        tag = self.env["account.account.tag"].create(
            {"name": "Wizard test tag", "applicability": "accounts"}
        )
        account.tag_ids = [Command.set(tag.ids)]
        # diff_fields should synthesize "" for the missing template value.
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        result = wizard.diff_fields(
            self.chart_template_data["account.account"][
                list(self.chart_template_data["account.account"])[0]
            ],
            account,
        )
        self.assertIn("tag_ids", result)
        self.assertEqual(result["tag_ids"], "")

    def test_09_boolean_drift_uses_field_default(self):
        """A boolean absent from the template compares to the field default,
        not blindly to False."""
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        # vat_required defaults to False; flip it to True to simulate drift.
        fp.auto_apply = False
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # Template data for this fp omits vat_required (empty cell in CSV).
        t_vals = self.chart_template_data["account.fiscal.position"][
            "template_generic_domestic_fiscal_position"
        ]
        result = wizard.diff_fields(t_vals, fp)
        self.assertIn("auto_apply", result)
        self.assertEqual(bool(result["auto_apply"]), True)
        # And: when the DB already matches the default, no drift.
        fp.auto_apply = True
        result = wizard.diff_fields(t_vals, fp)
        self.assertNotIn("auto_apply", result)

    def test_10_readonly_and_computed_skipped_in_post_loop(self):
        """Inverse/readonly m2m (replacing_tax_ids) and computed-editable
        (use_in_tax_closing) must not be flagged by the synthetic post-loop."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # sale_export_tax_template replaces sale_tax_template → the latter
        # gets a non-empty `replacing_tax_ids` by construction.
        src_tax = self._get_record_for_xml_id("sale_tax_template")
        self.assertTrue(src_tax.replacing_tax_ids)
        t_vals = self.chart_template_data["account.tax"]["sale_tax_template"]
        result = wizard.diff_fields(t_vals, src_tax)
        self.assertNotIn("replacing_tax_ids", result)
        # And a stored-computed-editable boolean must not be flagged either.
        rep_line = src_tax.repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        )[:1]
        self.assertTrue(rep_line)
        # Pass a template dict that doesn't mention use_in_tax_closing.
        result_rep = wizard.diff_fields({"repartition_type": "tax"}, rep_line)
        self.assertNotIn("use_in_tax_closing", result_rep)

    def test_11_m2m_command_list_diff_detected(self):
        """Previously the ORM-command-list branch compared `.sort() != .sort()`
        (both None), silently hiding every diff. A real tag drift must now
        be flagged."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # Synthesize a template dict whose tag_ids value is a command list
        # (that's what _deref_account_tags produces for the chart template).
        tag_a = self.env["account.account.tag"].create(
            {"name": "A", "applicability": "taxes"}
        )
        tag_b = self.env["account.account.tag"].create(
            {"name": "B", "applicability": "taxes"}
        )
        rep_line = self._get_record_for_xml_id(
            "sale_tax_template"
        ).repartition_line_ids.filtered(lambda r: r.repartition_type == "tax")[:1]
        self.assertTrue(rep_line)
        rep_line.tag_ids = [Command.set(tag_a.ids)]
        # Template expects [tag_b] (different from what the DB has).
        result = wizard.diff_fields({"tag_ids": [Command.set(tag_b.ids)]}, rep_line)
        self.assertIn("tag_ids", result)

    def test_12_missing_xml_id_note_format(self):
        """The 'Missing XML-ID' note must include both the expected xmlid
        and the ones currently attached."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax = self._get_record_for_xml_id("sale_tax_template")
        # Attach a foreign xmlid and drop the canonical one.
        model_data = self._get_model_data(tax)
        model_data.unlink()
        self.env["ir.model.data"].create(
            {
                "module": "base",
                "model": "account.tax",
                "name": "wizard_test_probe_xmlid",
                "res_id": tax.id,
            }
        )
        note = wizard._missing_xml_id_note(tax, "sale_tax_template")
        self.assertIn(f"account.{self.company.id}_sale_tax_template", note)
        self.assertIn("base.wizard_test_probe_xmlid", note)

    def test_13_diff_note_renders_boolean_and_m2o(self):
        """The per-field detail rendered by diff_notes should use the
        actual → expected form for booleans and m2o display names."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        fp.auto_apply = False
        note = wizard.diff_notes(
            self.chart_template_data["account.fiscal.position"][
                "template_generic_domestic_fiscal_position"
            ],
            fp,
        )
        self.assertIn("Detect Automatically", note)
        self.assertIn("False → True", note)

    def test_14_diff_note_label_for_fp_account_mapping(self):
        """Fiscal position mappings must render as `src → dest`, not the
        parent fiscal position's name (whose rec_name is `position_id`)."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        account_data = self.chart_template_data["account.account"]
        src = self._get_record_for_xml_id(list(account_data)[0])
        dest = self._get_record_for_xml_id(list(account_data)[1])
        fp.account_ids = [
            Command.create({"account_src_id": src.id, "account_dest_id": dest.id})
        ]
        # Template for this fp has no account_ids → the post-loop flags drift.
        note = wizard.diff_notes(
            self.chart_template_data["account.fiscal.position"][
                "template_generic_domestic_fiscal_position"
            ],
            fp,
        )
        self.assertIn(f"{src.display_name} → {dest.display_name}", note)
        self.assertIn("∅", note)  # expected side is empty

    def test_15_diff_note_commands_count_mismatch(self):
        """When template and DB disagree on the number of repartition lines,
        the detail surfaces `N record(s) → M record(s)` rather than a
        per-line breakdown."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax = self._get_record_for_xml_id("sale_tax_template")
        # Construct a synthetic template value that has one fewer line than
        # the DB. Modifying the real tax would trip Odoo's "exactly one
        # base line per side" constraint, so we exercise the renderer
        # directly via a crafted record_values dict.
        full = self.chart_template_data["account.tax"]["sale_tax_template"]
        trimmed = dict(full)
        trimmed["repartition_line_ids"] = list(full["repartition_line_ids"])[:-1]
        wizard.tax_field_ids += self.env["ir.model.fields"].search(
            [("model", "=", "account.tax"), ("name", "=", "repartition_line_ids")]
        )
        note = wizard.diff_notes(trimmed, tax)
        self.assertRegex(note, r"\d+ record\(s\) → \d+ record\(s\)")

    def test_16_m2m_command_link_branch(self):
        """Drift must be detected when the template value is expressed with
        `Command.link(...)` — exercises the LINK branch in the m2m
        command-list comparator."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tag_a = self.env["account.account.tag"].create(
            {"name": "Link A", "applicability": "taxes"}
        )
        tag_b = self.env["account.account.tag"].create(
            {"name": "Link B", "applicability": "taxes"}
        )
        rep_line = self._get_record_for_xml_id(
            "sale_tax_template"
        ).repartition_line_ids.filtered(lambda r: r.repartition_type == "tax")[:1]
        self.assertTrue(rep_line)
        rep_line.tag_ids = [Command.set(tag_a.ids)]
        # Template expects tag_b linked (not tag_a in DB).
        result = wizard.diff_fields({"tag_ids": [Command.link(tag_b.id)]}, rep_line)
        self.assertIn("tag_ids", result)
        # And no drift when the LINK target matches the DB.
        rep_line.tag_ids = [Command.set(tag_b.ids)]
        result = wizard.diff_fields({"tag_ids": [Command.link(tag_b.id)]}, rep_line)
        self.assertNotIn("tag_ids", result)

    def test_17_diff_note_label_branches(self):
        """`_diff_note_label` must render src→dest for fp mappings,
        `document_type/repartition_type factor%` for repartition lines,
        and fall back to `display_name` for anything else."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # fp.account branch
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        account_data = self.chart_template_data["account.account"]
        src = self._get_record_for_xml_id(list(account_data)[0])
        dest = self._get_record_for_xml_id(list(account_data)[1])
        fp.account_ids = [
            Command.create({"account_src_id": src.id, "account_dest_id": dest.id})
        ]
        mapping = fp.account_ids[:1]
        self.assertTrue(mapping)
        self.assertEqual(
            wizard._diff_note_label(mapping),
            f"{src.display_name} → {dest.display_name}",
        )
        # tax.repartition.line branch
        rep = self._get_record_for_xml_id(
            "sale_tax_template"
        ).repartition_line_ids.filtered(lambda r: r.repartition_type == "tax")[:1]
        self.assertTrue(rep)
        self.assertEqual(
            wizard._diff_note_label(rep),
            f"{rep.document_type}/{rep.repartition_type} {rep.factor_percent:g}%",
        )
        # default branch — any other model falls through to display_name.
        tag = self.env["account.account.tag"].create(
            {"name": "LabelDefault", "applicability": "accounts"}
        )
        self.assertEqual(wizard._diff_note_label(tag), tag.display_name)

    def test_18_diff_note_expected_m2x_names_branches(self):
        """`_diff_note_expected_m2x_names` handles xmlid strings, SET and
        LINK command lists, and returns [] for unknown shapes."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # SET command
        tag_a = self.env["account.account.tag"].create(
            {"name": "Set-A", "applicability": "taxes"}
        )
        tag_b = self.env["account.account.tag"].create(
            {"name": "Set-B", "applicability": "taxes"}
        )
        names = wizard._diff_note_expected_m2x_names(
            [Command.set([tag_b.id, tag_a.id])], "account.account.tag"
        )
        self.assertEqual(names, sorted([tag_a.display_name, tag_b.display_name]))
        # LINK command (appended one by one)
        names = wizard._diff_note_expected_m2x_names(
            [Command.link(tag_a.id), Command.link(tag_b.id)],
            "account.account.tag",
        )
        self.assertEqual(names, sorted([tag_a.display_name, tag_b.display_name]))
        # xmlid string — short form gets the company prefix applied
        fp_xmlids = ",".join(
            [
                "template_generic_domestic_fiscal_position",
                "template_generic_export_fiscal_position",
            ]
        )
        names = wizard._diff_note_expected_m2x_names(
            fp_xmlids, "account.fiscal.position"
        )
        self.assertEqual(len(names), 2)
        # Unknown value / missing comodel → empty
        self.assertEqual(wizard._diff_note_expected_m2x_names(42, None), [])
        self.assertEqual(wizard._diff_note_expected_m2x_names(None, None), [])

    def test_19_diff_note_sub_detail_branches(self):
        """`_diff_note_sub_detail` renders sub-field diffs for m2o, m2m
        and scalar sub-fields."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        rep = self._get_record_for_xml_id(
            "sale_tax_template"
        ).repartition_line_ids.filtered(lambda r: r.repartition_type == "tax")[:1]
        tag = self.env["account.account.tag"].create(
            {"name": "Sub-Tag", "applicability": "taxes"}
        )
        # m2o path: expected_v is an xmlid string
        new_account = self._get_record_for_xml_id(
            list(self.chart_template_data["account.account"])[0]
        )
        model_data = self.env["ir.model.data"].search(
            [("model", "=", "account.account"), ("res_id", "=", new_account.id)]
        )
        short_xmlid = model_data.name.split("_", maxsplit=1)[1]
        detail = wizard._diff_note_sub_detail(
            {"account_id": short_xmlid, "factor_percent": 50.0},
            rep,
            ["account_id", "factor_percent"],
        )
        self.assertIn(f"account_id '{rep.account_id.display_name}'", detail)
        self.assertIn(f"'{new_account.display_name}'", detail)
        self.assertIn("factor_percent", detail)
        self.assertIn(f"'{rep.factor_percent}'", detail)
        self.assertIn("'50.0'", detail)
        # m2m path: expected_v is a command list
        rep.tag_ids = [Command.set([])]
        detail = wizard._diff_note_sub_detail(
            {"tag_ids": [Command.set([tag.id])]}, rep, ["tag_ids"]
        )
        self.assertIn(f"tag_ids [∅] → [{tag.display_name}]", detail)

    def test_20_diff_note_commands_branches(self):
        """`_diff_note_commands` counts SET/LINK/CREATE correctly and picks
        the right branch: count mismatch, per-line detail, or generic
        fallback."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax = self._get_record_for_xml_id("sale_tax_template")
        field = tax._fields["repartition_line_ids"]
        actual = tax.repartition_line_ids
        # SET branch — expected_count = len(cmd[2]); DB has 4 lines, template says 8.
        synthetic = [
            999_001,
            999_002,
            999_003,
            999_004,
            999_005,
            999_006,
            999_007,
            999_008,
        ]
        result = wizard._diff_note_commands(field, actual, [Command.set(synthetic)])
        self.assertEqual(
            result,
            f"{len(actual)} record(s) → {len(synthetic)} record(s)",
        )
        # LINK branch — two LINK commands count as 2 (so count mismatch again).
        result = wizard._diff_note_commands(
            field, actual, [Command.link(999_001), Command.link(999_002)]
        )
        self.assertIn(f"{len(actual)} record(s) → 2 record(s)", result)
        # CREATE branch with same count and a real sub-diff → per-line format.
        # Build a template with the same count as actual but with a drifted
        # factor_percent on the first line.
        template_lines = [
            Command.create(
                {
                    "repartition_type": r.repartition_type,
                    "document_type": r.document_type,
                    "factor_percent": r.factor_percent,
                }
            )
            for r in actual
        ]
        # Flip factor_percent on the first line from 100 → 42 to force drift.
        template_lines[0][2]["factor_percent"] = 42.0
        result = wizard._diff_note_commands(field, actual, template_lines)
        self.assertIn("#1:", result)
        self.assertIn("factor_percent", result)
        # Same count, no drift at all → generic fallback message.
        template_lines_nodiff = [
            Command.create(
                {
                    "repartition_type": r.repartition_type,
                    "document_type": r.document_type,
                    "factor_percent": r.factor_percent,
                }
            )
            for r in actual
        ]
        result = wizard._diff_note_commands(field, actual, template_lines_nodiff)
        self.assertEqual(
            result,
            f"{len(actual)} record(s) → differs from template",
        )

    def test_21_diff_note_m2o_branches(self):
        """`_diff_note_m2o` renders actual/expected display names whether
        the template value is an xmlid string, an int database id, or
        points to something that can't be resolved."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax = self._get_record_for_xml_id("sale_tax_template")
        field = tax._fields["tax_group_id"]
        actual = tax.tax_group_id
        # Resolvable xmlid → expected side uses the record's display_name.
        model_data = self.env["ir.model.data"].search(
            [("model", "=", "account.tax.group"), ("res_id", "=", actual.id)]
        )[:1]
        self.assertTrue(model_data)
        short_xmlid = model_data.name.split("_", maxsplit=1)[1]
        result = wizard._diff_note_m2o(field, actual, short_xmlid)
        self.assertEqual(result, f"'{actual.display_name}' → '{actual.display_name}'")
        # Unresolvable xmlid → echo the raw string on the expected side.
        result = wizard._diff_note_m2o(field, actual, "does_not_exist_xmlid")
        self.assertEqual(result, f"'{actual.display_name}' → 'does_not_exist_xmlid'")
        # Int expected pointing to an existing record → display_name.
        other_group = self.env["account.tax.group"].create({"name": "M2O-Int-Probe"})
        result = wizard._diff_note_m2o(field, actual, other_group.id)
        self.assertEqual(
            result, f"'{actual.display_name}' → '{other_group.display_name}'"
        )
        # Int expected pointing to a non-existent id → stringified id.
        missing_id = 2_000_000_000
        result = wizard._diff_note_m2o(field, actual, missing_id)
        self.assertEqual(result, f"'{actual.display_name}' → '{missing_id}'")
        # None/empty expected → empty expected side.
        result = wizard._diff_note_m2o(field, actual, None)
        self.assertEqual(result, f"'{actual.display_name}' → ''")
        # Empty actual + xmlid expected → empty actual side.
        empty = self.env["account.tax.group"]
        result = wizard._diff_note_m2o(field, empty, short_xmlid)
        self.assertEqual(result, f"'' → '{actual.display_name}'")

    def test_22_diff_note_commands_caps_at_three_sub_diffs(self):
        """The per-line sub-diff enumeration must stop after 3 entries to
        keep the note readable even when more lines drifted."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax = self._get_record_for_xml_id("sale_tax_template")
        field = tax._fields["repartition_line_ids"]
        actual = tax.repartition_line_ids
        self.assertGreaterEqual(len(actual), 4)
        # Build a template that flips factor_percent on every line → 4+
        # differing sub-records, but the renderer should only list 3.
        template_lines = [
            Command.create(
                {
                    "repartition_type": r.repartition_type,
                    "document_type": r.document_type,
                    "factor_percent": (r.factor_percent or 0) + 1,
                }
            )
            for r in actual
        ]
        result = wizard._diff_note_commands(field, actual, template_lines)
        self.assertEqual(result.count("#"), 3)

    def test_23_account_group_code_prefix_end_drift_note(self):
        """When the template's code_prefix_end differs from the DB, the
        wizard must append a per-field bullet with the actual/expected
        values under the "Differences in these fields:" header."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        t_data = {
            "test_group_end_drift": {
                "name": "End Drift Group",
                "code_prefix_start": "643",
                "code_prefix_end": "648",
            },
        }
        group = self.env["account.group"].create(
            {
                "name": "End Drift Group",
                "code_prefix_start": "643",
                # Same as start — template expects "648".
                "code_prefix_end": "643",
                "company_id": self.company.id,
            }
        )
        self.env["ir.model.data"].create(
            {
                "name": f"{self.company.id}_test_group_end_drift",
                "module": "account",
                "model": "account.group",
                "res_id": group.id,
            }
        )
        wizard._find_account_groups(t_data)
        updated = wizard.account_group_ids.filtered(lambda r: r.type == "updated")
        self.assertEqual(len(updated), 1)
        label = group._fields["code_prefix_end"].get_description(self.env)["string"]
        self.assertIn("Differences in these fields:", updated.notes)
        self.assertIn(f"- {label}: '643' → '648'", updated.notes)

    def test_24_account_group_code_prefix_end_drift_without_header(self):
        """When `diff_notes` returns no drift (template omits
        `code_prefix_end`, so the main loop skips it) but the local
        `code_prefix_end` normalization still disagrees with the DB, the
        renderer must prepend the "Differences in these fields:" header
        itself."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # Template omits code_prefix_end entirely → normalizes to
        # code_prefix_start ("700"); DB has "750".
        t_data = {
            "test_group_end_only": {
                "name": "End Only Group",
                "code_prefix_start": "700",
            },
        }
        group = self.env["account.group"].create(
            {
                "name": "End Only Group",
                "code_prefix_start": "700",
                "code_prefix_end": "750",
                "company_id": self.company.id,
            }
        )
        self.env["ir.model.data"].create(
            {
                "name": f"{self.company.id}_test_group_end_only",
                "module": "account",
                "model": "account.group",
                "res_id": group.id,
            }
        )
        wizard._find_account_groups(t_data)
        updated = wizard.account_group_ids.filtered(lambda r: r.type == "updated")
        self.assertEqual(len(updated), 1)
        # The header must be emitted locally (diff_notes returned empty).
        self.assertTrue(updated.notes.startswith("Differences in these fields:"))
        self.assertIn("'750' → '700'", updated.notes)

    def test_25_account_group_missing_xml_id(self):
        """A matched-but-xmlid-less account group must be flagged as
        "updated" with the `Missing XML-ID` note, and the note must be
        appended (not overwriting) when another drift already produced
        a header."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # Template says the group should be xmlid `test_group_missing`, and
        # the DB has a matching record but with no xml_id at all.
        t_data = {
            "test_group_missing": {
                "name": "Missing XmlId Group",
                "code_prefix_start": "810",
                "code_prefix_end": "819",
            },
        }
        self.env["account.group"].create(
            {
                "name": "Missing XmlId Group",
                # code_prefix_end drifted so diff_notes also produces a header.
                "code_prefix_start": "810",
                "code_prefix_end": "810",
                "company_id": self.company.id,
            }
        )
        wizard._find_account_groups(t_data)
        updated = wizard.account_group_ids.filtered(lambda r: r.type == "updated")
        self.assertEqual(len(updated), 1)
        self.assertIn("Missing XML-ID", updated.notes)
        self.assertIn(f"account.{self.company.id}_test_group_missing", updated.notes)

    def test_26_tax_group_missing_xml_id(self):
        """A tax group matched by a non-xmlid field must be flagged as
        "updated" with the `Missing XML-ID` note from
        `_find_tax_groups`."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        tax_group = self._get_record_for_xml_id("tax_group_15")
        # Drop the xmlid so matching must fall back to the `name` field.
        self._get_model_data(tax_group).unlink()
        wizard._find_tax_groups(
            {
                "tax_group_15": self.chart_template_data["account.tax.group"][
                    "tax_group_15"
                ],
            }
        )
        updated = wizard.tax_group_ids.filtered(
            lambda r: r.update_tax_group_id == tax_group
        )
        self.assertEqual(len(updated), 1)
        self.assertIn("Missing XML-ID", updated.notes)
        self.assertIn(f"account.{self.company.id}_tax_group_15", updated.notes)

    def test_27_fiscal_position_missing_xml_id(self):
        """A fiscal position matched by a non-xmlid field must be flagged
        as "updated" with the `Missing XML-ID` note from
        `_find_fiscal_positions`."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        # Drop the xmlid so matching must fall back to the `name` field.
        self._get_model_data(fp).unlink()
        wizard._find_fiscal_positions(
            {
                "template_generic_domestic_fiscal_position": self.chart_template_data[
                    "account.fiscal.position"
                ]["template_generic_domestic_fiscal_position"],
            }
        )
        updated = wizard.fiscal_position_ids.filtered(
            lambda r: r.update_fiscal_position_id == fp
        )
        self.assertEqual(len(updated), 1)
        self.assertIn("Missing XML-ID", updated.notes)
        self.assertIn(
            f"account.{self.company.id}_template_generic_domestic_fiscal_position",
            updated.notes,
        )

    def test_28_diff_note_translation_shows_correct_language(self):
        """When a translatable field drifts only in a non-English variant,
        the diff note must show the per-language values rather than the
        identical English ones."""
        self.env["res.lang"]._activate_lang("fr_FR")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        account_data = self.chart_template_data["account.account"]
        account_xml_id = list(account_data)[0]
        account = self._get_record_for_xml_id(account_xml_id)
        # English value stays in sync; only French diverges.
        english_name = account.with_context(lang="en_US").name
        account.with_context(lang="fr_FR").name = "Compte dérivé"
        record_values = {
            "name": english_name,
            "name@fr": "Compte attendu",
        }
        note = wizard.diff_notes(record_values, account)
        self.assertIn("[fr]", note)
        self.assertIn("Compte dérivé", note)
        self.assertIn("Compte attendu", note)
        # Sanity: don't render the misleading English-only comparison.
        self.assertNotIn(f"'{english_name}' → '{english_name}'", note)

    def test_27b_get_chart_template_data_drops_missing_translations(self):
        """When the template has no translation for a language, the
        per-language key must not fall back to the English source — that
        falsely flags user-provided translations as drift."""
        self.env["res.lang"]._activate_lang("nl_NL")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        # generic_coa template carries no nl translations, so the per-
        # language keys for nl must not appear at all.
        data = wizard._get_chart_template_data()
        for record_values in data["account.fiscal.position"].values():
            self.assertNotIn(
                "name@nl",
                record_values,
                "Missing template translations must not be backfilled with"
                " the English value",
            )

    def test_27c_user_translation_without_template_translation_is_not_drift(self):
        """A DB-side translation must not be reported as drifted when the
        template has no translation for that language."""
        self.env["res.lang"]._activate_lang("nl_NL")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        # User-set translation that has no counterpart in the template.
        fp.with_context(lang="nl_NL").name = "Binnenlands - test"
        record_values = wizard._get_chart_template_data()["account.fiscal.position"][
            "template_generic_domestic_fiscal_position"
        ]
        note = wizard.diff_notes(record_values, fp)
        self.assertNotIn(
            "[nl]",
            note,
            "Dutch translation should not be flagged when the template has"
            " no Dutch translation",
        )
        self.assertNotIn("Binnenlands - test", note)

    def test_27d_diff_note_renders_synthesized_boolean_expected(self):
        """When the post-loop synthesizes drift for a boolean missing from
        the template, the note must show the field's actual default as the
        expected value — not `False` from `bool(None)`."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        account_data = self.chart_template_data["account.account"]
        account = self._get_record_for_xml_id(list(account_data)[0])
        account.active = False
        record_values = dict(account_data[list(account_data)[0]])
        record_values.pop("active", None)
        note = wizard.diff_notes(record_values, account)
        self.assertIn("Active", note)
        self.assertIn("False → True", note)
        self.assertNotIn("False → False", note)

    def test_28a_no_drift_when_only_missing_translation_would_differ(self):
        """A template translation for a language the DB never had stored
        must not be flagged as drift — it's a translation the user never
        created, not drift in a translation they did."""
        self.env["res.lang"]._activate_lang("fr_FR")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        account_data = self.chart_template_data["account.account"]
        account = self._get_record_for_xml_id(list(account_data)[0])
        english_name = account.with_context(lang="en_US").name
        # No French translation set on the DB record.
        record_values = {
            "name": english_name,
            "name@fr": "Compte attendu",
        }
        diff = wizard.diff_fields(record_values, account)
        self.assertNotIn(
            "name@fr",
            diff,
            "Missing-translation case must not produce a drift entry",
        )
        note = wizard.diff_notes(record_values, account)
        self.assertNotIn("[fr]", note)
        self.assertNotIn("Compte attendu", note)

    def test_28c_english_drift_does_not_drag_in_missing_translation(self):
        """When English drifts and a non-English template translation
        exists but the DB never stored that language, the missing-language
        line must not appear in the rendered note."""
        self.env["res.lang"]._activate_lang("nl_NL")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        account_data = self.chart_template_data["account.account"]
        account = self._get_record_for_xml_id(list(account_data)[0])
        # English drifts; no Dutch translation has ever been stored.
        account.with_context(lang="en_US").name = "Undistributed Profits/Losses"
        record_values = {
            "name": "Profit or Loss Appropriation",
            "name@nl": "Resultaatverwerking",
        }
        diff = wizard.diff_fields(record_values, account)
        self.assertIn("name", diff)
        self.assertNotIn("name@nl", diff)
        note = wizard.diff_notes(record_values, account)
        self.assertIn("Undistributed Profits/Losses", note)
        self.assertIn("Profit or Loss Appropriation", note)
        self.assertNotIn("[nl]", note)
        self.assertNotIn("Resultaatverwerking", note)

    def test_28b_diff_note_translation_html_field_strips_tags(self):
        """`_diff_note_translation_detail` must strip HTML tags from both
        actual and expected values on an HTML translatable field so the
        bullet stays readable.
        """
        self.env["res.lang"]._activate_lang("fr_FR")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        fp = self._get_record_for_xml_id("template_generic_domestic_fiscal_position")
        # Use the actual stored value as the "actual" side: the per-lang
        # write path on Html(translate=True) makes it unreliable to assume
        # the en/fr slots stay independent, so we work directly with what
        # ends up in the record.
        fp.with_context(lang="fr_FR").note = "<p>Note <b>actuelle</b></p>"
        field = fp._fields["note"]
        detail = wizard._diff_note_translation_detail(
            field,
            fp,
            {"note@fr": "<p>Note <i>attendue</i></p>"},
            ["note@fr"],
        )
        self.assertIn("[fr]", detail)
        # Inner content only — tags must be stripped on both sides.
        self.assertIn("Note actuelle", detail)
        self.assertIn("Note attendue", detail)
        self.assertNotIn("<p>", detail)
        self.assertNotIn("<b>", detail)
        self.assertNotIn("<i>", detail)

    def test_29_diff_note_translation_shows_both_languages(self):
        """When both English and a translation differ, both per-language
        lines must appear."""
        self.env["res.lang"]._activate_lang("fr_FR")
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        account_data = self.chart_template_data["account.account"]
        account_xml_id = list(account_data)[0]
        account = self._get_record_for_xml_id(account_xml_id)
        account.with_context(lang="en_US").name = "Drift EN"
        account.with_context(lang="fr_FR").name = "Drift FR"
        record_values = {
            "name": "Expected EN",
            "name@fr": "Expected FR",
        }
        note = wizard.diff_notes(record_values, account)
        self.assertIn("[en]", note)
        self.assertIn("[fr]", note)
        self.assertIn("Drift EN", note)
        self.assertIn("Expected EN", note)
        self.assertIn("Drift FR", note)
        self.assertIn("Expected FR", note)
