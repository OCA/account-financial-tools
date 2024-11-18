# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account_chart_update.tests.common import TestAccountChartUpdateCommon

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class TestAccountChartUpdate(TestAccountChartUpdateCommon):
    def _get_record_for_xml_id(self, xml_id):
        return self.env.ref(f"account.{self.company.id}_{xml_id}")

    @mute_logger("odoo.models.unlink")
    def test_chart_update_01(self):
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        # Test ir.model.fields _compute_display_name
        field = wizard.fp_field_ids[:1]
        name = field.with_context(account_chart_update=True).display_name
        expected_name = f"{field.field_description} ({field.name})"
        self.assertEqual(name, expected_name)
        self.assertNotEqual(field.display_name, expected_name)
        # Test no changes
        self.assertEqual(wizard.state, "ready")
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        self.assertFalse(wizard.fiscal_position_ids)
        wizard.unlink()
        # Check that no action is performed if the option is not selected
        wizard_vals = self.wizard_vals.copy()
        wizard_vals.update(
            {
                "update_tax": False,
                "update_account": False,
                "update_fiscal_position": False,
            }
        )
        wizard = self.wizard_obj.create(wizard_vals)
        wizard.action_find_records()
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        self.assertFalse(wizard.fiscal_position_ids)
        # We delete the existing records so that they appear "to be created".
        domain = [("company_id", "=", self.company.id)]
        ip = self.env["ir.property"].sudo()
        self.env["account.tax"].search(domain).unlink()
        accounts = self.env["account.account"].search(domain)
        values = [f"account.account,{a_id}" for a_id in accounts.ids]
        ip.search([("value_reference", "in", values)]).unlink()
        journals = self.env["account.journal"].search(domain)
        values = [f"account.journal,{j_id}" for j_id in journals.ids]
        ip.search([("value_reference", "in", values)]).unlink()
        journals.unlink()
        accounts.unlink()
        self.env["account.fiscal.position"].search(domain).unlink()
        self.env["account.group"].search(domain).unlink()
        wizard.unlink()
        # Now do the real one for detecting additions
        wizard = self.wizard_obj.create(self.wizard_vals)
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
        fp_data = self.chart_template_data["fiscal.position"]
        self.assertEqual(len(wizard.fiscal_position_ids), len(fp_data))
        # generic_coa has no account.fiscal.position.data
        fp_types = wizard.fiscal_position_ids.mapped("type")
        self.assertNotIn("new", fp_types)
        self.assertNotIn("updated", fp_types)
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
        self.assertTrue(new_account)
        wizard.unlink()
        # Update objects
        new_account.name = "Account name (updated)"
        new_tax.name = "Tax name (updated)"
        new_tax_group = self.env["account.tax.group"].create({"name": "Test 1"})
        new_tax.tax_group_id = new_tax_group
        repartition = new_tax.repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        )[0]
        repartition.account_id = new_account.id
        wizard = self.wizard_obj.create(self.wizard_vals)
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
        wizard = self.wizard_obj.create(self.wizard_vals)
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
    def test_chart_update_02(self):
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
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.tax_ids.update_tax_id, new_tax)
        self.assertEqual(wizard.tax_ids.type, "updated")
        self.assertEqual(wizard.account_ids.update_account_id, new_account)
        self.assertEqual(wizard.account_ids.type, "updated")
        wizard.action_update_records()
        self.assertEqual(wizard.updated_taxes, 1)
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(new_tax.name, tax_data_0["name"])
        self.assertEqual(new_account.code, wizard.padded_code(account_data_0["code"]))
        # Test match by another field, there is no match by XML-ID
        self._get_model_data(new_tax).unlink()
        self._get_model_data(new_account).unlink()
        new_account.name = "Test 2 account name changed"
        wizard = self.wizard_obj.create(self.wizard_vals)
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
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.account_ids.update_account_id, new_account)
        self.assertEqual(wizard.account_ids.type, "updated")
        wizard.action_update_records()
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(new_account.code, wizard.padded_code(account_data_0["code"]))
        wizard.unlink()
