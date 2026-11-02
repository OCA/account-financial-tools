# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.account.models.chart_template import AccountChartTemplate
from odoo.addons.account_chart_update.tests.common import TestAccountChartUpdateCommon

_logger = logging.getLogger(__name__)


@tagged("-at_install", "post_install")
class TestAccountChartUpdate(TestAccountChartUpdateCommon):
    def _get_record_for_xml_id(self, xml_id):
        # To read company-dependent fields correctly
        return self.env.ref(f"account.{self.company.id}_{xml_id}").with_company(
            self.company
        )

    def _get_taxes_only_wizard_vals(self, **extra):
        """Wizard values restricted to taxes, to keep the checks focused."""
        vals = dict(
            self.wizard_vals,
            update_account=False,
            update_account_group=False,
            update_tax_group=False,
            update_fiscal_position=False,
        )
        vals.update(extra)
        return vals

    def _get_tax_xml_id_with_repartition_account(self):
        """XML-ID of a template tax whose repartition lines carry an account."""
        return next(
            xml_id
            for xml_id, values in self.chart_template_data["account.tax"].items()
            if any(
                line[2].get("account_id")
                for line in values.get("repartition_line_ids", [])
            )
        )

    @contextmanager
    def _template_data_with(self, extra):
        """Complete the data the chart template exposes with ``extra``.

        The generic chart of accounts has neither grouped taxes nor tags on its
        repartition lines, so there is no way of exercising those from the real
        data. The template is a pure data provider in this Odoo version, so it
        is completed here the same way ``account`` tests its own loader.
        """
        data = self.env["account.chart.template"]._get_chart_template_data(
            "generic_coa"
        )
        for model, records in extra.items():
            for xml_id, values in records.items():
                data[model][xml_id].update(values)
        with patch.object(
            AccountChartTemplate,
            "_get_chart_template_data",
            side_effect=lambda self, template_code: data,
            autospec=True,
        ):
            yield data

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

    def test_03_installed_charts(self):
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        chart_template_installed = wizard._chart_template_selection()
        all_chart_templates = self.env[
            "account.chart.template"
        ]._get_chart_template_mapping()
        only_installed = list(
            filter(lambda x: x["installed"], all_chart_templates.values())
        )
        self.assertEqual(len(chart_template_installed), len(only_installed))

    def test_04_continue_on_errors(self):
        """A reference that cannot be resolved must not pass unnoticed.

        The loader of this Odoo version drops the field it could not resolve
        and only writes a warning to the log, so the wizard would otherwise
        report a successful update of a tax that lost its accounts.
        """
        tax = self._get_record_for_xml_id(
            self._get_tax_xml_id_with_repartition_account()
        )
        repartition = tax.repartition_line_ids.filtered(lambda x: x.account_id)
        account = repartition.account_id
        # Leave the account without XML-ID, so the template can no longer point
        # at it, and make the tax differ from the template so it is updated.
        self._get_model_data(account).unlink()
        repartition.account_id = False
        wizard = self.wizard_obj.with_company(self.company).create(
            self._get_taxes_only_wizard_vals()
        )
        wizard.action_find_records()
        self.assertEqual(wizard.tax_ids.update_tax_id, tax)
        with self.assertRaises(UserError) as error:
            wizard.action_update_records()
        self.assertIn("tax_received", str(error.exception))
        # Asking to continue applies what can be applied and keeps the log
        wizard.continue_on_errors = True
        wizard.action_update_records()
        self.assertEqual(wizard.state, "done")
        self.assertIn("tax_received", wizard.log)
        self.assertFalse(tax.repartition_line_ids.account_id)

    def test_05_tax_repartition_line_account(self):
        """The account set by hand on a repartition line can be preserved."""
        tax = self._get_record_for_xml_id(
            self._get_tax_xml_id_with_repartition_account()
        )
        repartition = tax.repartition_line_ids.filtered(lambda x: x.account_id)[0]
        template_account = repartition.account_id
        custom_account = self.env["account.account"].search(
            [
                ("company_ids", "in", self.company.ids),
                ("id", "!=", template_account.id),
            ],
            limit=1,
        )
        repartition.account_id = custom_account
        # Excluded: the difference is not even reported
        wizard = self.wizard_obj.with_company(self.company).create(
            self._get_taxes_only_wizard_vals(update_tax_repartition_line_account=False)
        )
        wizard.action_find_records()
        self.assertFalse(wizard.tax_ids)
        wizard.unlink()
        # Included (the default): the account of the template is restored,
        # updating the existing line instead of replacing the whole set
        wizard = self.wizard_obj.with_company(self.company).create(
            self._get_taxes_only_wizard_vals()
        )
        wizard.action_find_records()
        self.assertEqual(wizard.tax_ids.update_tax_id, tax)
        wizard.action_update_records()
        self.assertEqual(repartition.account_id, template_account)
        self.assertIn(repartition, tax.repartition_line_ids)

    def test_06_tax_repartition_line_tags(self):
        """The tags set by hand on a repartition line can be preserved."""
        tag_vals = {"applicability": "taxes", "country_id": self.company.country_id.id}
        template_tag = self.env["account.account.tag"].create(
            dict(tag_vals, name="Template tag")
        )
        custom_tag = self.env["account.account.tag"].create(
            dict(tag_vals, name="Custom tag")
        )
        tax_xml_id = self._get_tax_xml_id_with_repartition_account()
        tax = self._get_record_for_xml_id(tax_xml_id)
        tax.repartition_line_ids[0].tag_ids = custom_tag
        template_lines = self.chart_template_data["account.tax"][tax_xml_id][
            "repartition_line_ids"
        ]
        extra = {
            "account.tax": {
                tax_xml_id: {
                    "repartition_line_ids": [
                        Command.create(
                            dict(line[2], tag_ids=[Command.set(template_tag.ids)])
                        )
                        for line in template_lines
                    ]
                }
            }
        }
        with self._template_data_with(extra):
            # Excluded: the difference is not even reported
            wizard = self.wizard_obj.with_company(self.company).create(
                self._get_taxes_only_wizard_vals(update_tax_repartition_line_tags=False)
            )
            wizard.action_find_records()
            self.assertFalse(wizard.tax_ids)
            wizard.unlink()
            # Included (the default): the tags of the template are applied
            wizard = self.wizard_obj.with_company(self.company).create(
                self._get_taxes_only_wizard_vals()
            )
            wizard.action_find_records()
            self.assertEqual(wizard.tax_ids.update_tax_id, tax)
            wizard.action_update_records()
        self.assertEqual(tax.repartition_line_ids.tag_ids, template_tag)

    def test_07_check_consistency_children_taxes(self):
        """A grouped tax cannot be created without the taxes it groups."""
        extra = {
            "account.tax": {
                "test_child_tax": {
                    "name": "Test child tax",
                    "amount": 5,
                    "type_tax_use": "sale",
                },
                "test_group_tax": {
                    "name": "Test group tax",
                    "amount": 0,
                    "amount_type": "group",
                    "type_tax_use": "sale",
                    "children_tax_ids": "test_child_tax",
                },
            }
        }
        with self._template_data_with(extra):
            wizard = self.wizard_obj.with_company(self.company).create(
                self._get_taxes_only_wizard_vals()
            )
            wizard.action_find_records()
            new_taxes = wizard.tax_ids.filtered(lambda x: x.type == "new")
            self.assertEqual(
                set(new_taxes.mapped("xml_id")), {"test_child_tax", "test_group_tax"}
            )
            # Excluding the child from the selection is rejected, naming the
            # parent, before anything is written
            new_taxes.filtered(lambda x: x.xml_id == "test_child_tax").unlink()
            with self.assertRaises(UserError) as error:
                wizard.action_update_records()
            self.assertIn("test_group_tax", str(error.exception))
            # Keeping both, the grouped tax is created with its children
            wizard.unlink()
            wizard = self.wizard_obj.with_company(self.company).create(
                self._get_taxes_only_wizard_vals()
            )
            wizard.action_find_records()
            wizard.action_update_records()
        group_tax = self._get_record_for_xml_id("test_group_tax")
        self.assertEqual(
            group_tax.children_tax_ids, self._get_record_for_xml_id("test_child_tax")
        )
