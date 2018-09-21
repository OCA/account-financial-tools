# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import common


class TestAccountChartUpdate(common.HttpCase):
    at_install = False
    post_install = True

    def _create_xml_id(self, record):
        return self.env['ir.model.data'].create({
            'module': 'account_chart_update',
            'name': "%s-%s" % (record._table, record.id),
            'model': record._name,
            'res_id': record.id,
        })

    def _create_account_tmpl(self, name, code, user_type, chart_template):
        record = self.env['account.account.template'].create({
            'name': name,
            'code': code,
            'user_type_id': user_type.id,
            'chart_template_id': chart_template and chart_template.id,
        })
        self._create_xml_id(record)
        return record

    def _create_tax_tmpl(self, name, chart_template):
        record = self.env['account.tax.template'].create({
            'name': name,
            'amount': 0,
            'chart_template_id': chart_template.id,
            'tax_group_id': self.env.ref('account.tax_group_taxes').id,
        })
        self._create_xml_id(record)
        return record

    def _create_fp_tmpl(self, name, chart_template):
        record = self.env['account.fiscal.position.template'].create({
            'name': name,
            'chart_template_id': chart_template.id,
        })
        self._create_xml_id(record)
        return record

    def setUp(self):
        super(TestAccountChartUpdate, self).setUp()
        # Make sure user is in English
        self.env.user.lang = 'en_US'
        self.account_type = self.env['account.account.type'].create({
            'name': 'Test account_chart_update account type',
        })
        self.account_template = self._create_account_tmpl(
            'Test', '100000', self.account_type, False,
        )
        self.chart_template = self.env['account.chart.template'].create({
            'name': 'Test account_chart_update chart',
            'currency_id': self.env.ref('base.EUR').id,
            'code_digits': 6,
            'transfer_account_id': self.account_template.id,
        })
        self.account_template.chart_template_id = self.chart_template.id
        self.account_template_pl = self._create_account_tmpl(
            'Undistributed Profits/Losses', '999999',
            self.env.ref("account.data_unaffected_earnings"),
            self.chart_template,
        )
        self.tax_template = self._create_tax_tmpl(
            'Test tax', self.chart_template,
        )
        self.fp_template = self._create_fp_tmpl('Test fp', self.chart_template)
        self.fp_template_tax = self.env[
            'account.fiscal.position.tax.template'
        ].create({
            'tax_src_id': self.tax_template.id,
            'position_id': self.fp_template.id,
        })
        self._create_xml_id(self.fp_template_tax)
        self.fp_template_account = self.env[
            'account.fiscal.position.account.template'
        ].create({
            'account_src_id': self.account_template.id,
            'account_dest_id': self.account_template.id,
            'position_id': self.fp_template.id,
        })
        self._create_xml_id(self.fp_template_account)
        self.tax_group = self.env['account.tax.group'].create({
            'name': 'Test tax group',
        })
        self.account_tag_1 = self.env['account.account.tag'].create({
            'name': 'Test account tag 1',
        })
        self.account_tag_2 = self.env['account.account.tag'].create({
            'name': 'Test account tag 2',
        })
        self.company = self.env['res.company'].create({
            'name': 'Test account_chart_update company',
            'currency_id': self.chart_template.currency_id.id,
        })
        # Load chart of template into company
        wizard = self.env['wizard.multi.charts.accounts'].create({
            'company_id': self.company.id,
            'chart_template_id': self.chart_template.id,
            'code_digits': self.chart_template.code_digits,
            'transfer_account_id': self.account_template.id,
            'currency_id': self.chart_template.currency_id.id,
            'bank_account_code_prefix': '572',
            'cash_account_code_prefix': '570',
        })
        wizard.onchange_chart_template_id()
        wizard.execute()
        self.tax = self.env['account.tax'].search([
            ('name', '=', self.tax_template.name),
            ('company_id', '=', self.company.id),
        ])
        self.account = self.env['account.account'].search([
            ('code', '=', self.account_template.code),
            ('company_id', '=', self.company.id),
        ])
        self.fp = self.env['account.fiscal.position'].search([
            ('name', '=', self.fp_template.name),
            ('company_id', '=', self.company.id),
        ])
        # Prepare wizard values
        self.wizard_obj = self.env['wizard.update.charts.accounts']
        self.wizard_vals = {
            'company_id': self.company.id,
            'chart_template_id': self.chart_template.id,
            'code_digits': 6,
            'lang': 'en_US'
        }

    def test_chart_update(self):
        # Test no changes
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.state, 'ready')
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        self.assertFalse(wizard.fiscal_position_ids)
        wizard.unlink()
        # Add templates
        new_tax_tmpl = self._create_tax_tmpl(
            'Test tax 2', self.chart_template,
        )
        new_account_tmpl = self._create_account_tmpl(
            'Test account 2', '333333', self.account_type, self.chart_template,
        )
        new_fp = self._create_fp_tmpl('Test fp 2', self.chart_template)
        fp_template_tax = self.env[
            'account.fiscal.position.tax.template'
        ].create({
            'tax_src_id': self.tax_template.id,
            'position_id': new_fp.id,
        })
        self._create_xml_id(fp_template_tax)
        fp_template_account = self.env[
            'account.fiscal.position.account.template'
        ].create({
            'account_src_id': self.account_template.id,
            'account_dest_id': self.account_template.id,
            'position_id': new_fp.id,
        })
        self._create_xml_id(fp_template_account)
        # Check that no action is performed if the option is not selected
        wizard_vals = self.wizard_vals.copy()
        wizard_vals.update({
            'update_tax': False,
            'update_account': False,
            'update_fiscal_position': False,
        })
        wizard = self.wizard_obj.create(wizard_vals)
        wizard.action_find_records()
        self.assertFalse(wizard.tax_ids)
        self.assertFalse(wizard.account_ids)
        self.assertFalse(wizard.fiscal_position_ids)
        wizard.unlink()
        # Now do the real one for detecting additions
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertTrue(wizard.tax_ids)
        self.assertEqual(wizard.tax_ids.tax_id, new_tax_tmpl)
        self.assertEqual(wizard.tax_ids.type, 'new')
        self.assertTrue(wizard.account_ids)
        self.assertEqual(wizard.account_ids.account_id, new_account_tmpl)
        self.assertEqual(wizard.tax_ids.type, 'new')
        self.assertTrue(wizard.fiscal_position_ids)
        self.assertEqual(wizard.fiscal_position_ids.fiscal_position_id, new_fp)
        self.assertEqual(wizard.fiscal_position_ids.type, 'new')
        wizard.action_update_records()
        self.assertEqual(wizard.state, 'done')
        self.assertEqual(wizard.new_taxes, 1)
        self.assertEqual(wizard.new_accounts, 1)
        self.assertEqual(wizard.new_fps, 1)
        self.assertTrue(wizard.log)
        new_tax = self.env['account.tax'].search([
            ('name', '=', new_tax_tmpl.name),
            ('company_id', '=', self.company.id),
        ])
        self.assertTrue(new_tax)
        new_account = self.env['account.account'].search([
            ('code', '=', new_account_tmpl.code),
            ('company_id', '=', self.company.id),
        ])
        self.assertTrue(new_account)
        fp = self.env['account.fiscal.position'].search([
            ('name', '=', new_fp.name),
            ('company_id', '=', self.company.id),
        ])
        self.assertTrue(fp)
        self.assertTrue(fp.tax_ids)
        self.assertTrue(fp.account_ids)
        wizard.unlink()
        # Update objects
        self.tax_template.description = "Test description"
        self.tax_template.tax_group_id = self.tax_group.id
        self.tax_template.refund_account_id = new_account_tmpl.id
        self.account_template.name = "Other name"
        self.account_template.tag_ids = [
            (6, 0, [self.account_tag_1.id, self.account_tag_2.id]),
        ]
        self.fp_template.note = "Test note"
        self.fp_template.account_ids.account_dest_id = new_account_tmpl.id
        self.fp_template.tax_ids.tax_dest_id = self.tax_template.id
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertTrue(wizard.tax_ids)
        self.assertEqual(wizard.tax_ids.tax_id, self.tax_template)
        self.assertEqual(wizard.tax_ids.type, 'updated')
        self.assertTrue(wizard.account_ids)
        self.assertEqual(wizard.account_ids.account_id, self.account_template)
        self.assertEqual(wizard.account_ids.type, 'updated')
        self.assertTrue(wizard.fiscal_position_ids)
        self.assertTrue(wizard.fiscal_position_ids.type, 'updated')
        self.assertEqual(
            wizard.fiscal_position_ids.fiscal_position_id, self.fp_template,
        )
        self.assertEqual(wizard.fiscal_position_ids.type, 'updated')
        wizard.action_update_records()
        self.assertEqual(wizard.updated_taxes, 1)
        self.assertEqual(wizard.updated_accounts, 1)
        self.assertEqual(wizard.updated_fps, 1)
        self.assertEqual(self.tax.description, self.tax_template.description)
        self.assertEqual(self.tax.tax_group_id, self.tax_group)
        self.assertEqual(self.tax.refund_account_id, new_account)
        self.assertEqual(self.account.name, self.account_template.name)
        self.assertIn(self.account_tag_1, self.account.tag_ids)
        self.assertIn(self.account_tag_2, self.account.tag_ids)
        self.assertEqual(self.fp.note, self.fp_template.note)
        self.assertEqual(self.fp.account_ids.account_dest_id, new_account)
        self.assertEqual(self.fp.tax_ids.tax_dest_id, self.tax)
        wizard.unlink()
        # Remove objects
        new_tax_tmpl.unlink()
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertTrue(wizard.tax_ids)
        self.assertEqual(wizard.tax_ids.update_tax_id, new_tax)
        self.assertEqual(wizard.tax_ids.type, 'deleted')
        wizard.action_update_records()
        self.assertEqual(wizard.deleted_taxes, 1)
        self.assertFalse(new_tax.active)
        wizard.unlink()
        # Errors on account update
        self.account_template.reconcile = True
        self.env['account.move'].create({
            'name': 'Test move',
            'journal_id': self.env['account.journal'].search([
                ('company_id', '=', self.company.id),
            ], limit=1).id,
            'date': fields.Date.today(),
            'line_ids': [
                (0, 0, {
                    'account_id': self.account.id,
                    'name': 'Test move line',
                    'debit': 10,
                    'credit': 0,
                }),
                (0, 0, {
                    'account_id': self.account.id,
                    'name': 'Test move line2',
                    'debit': 0,
                    'credit': 10,
                }),
            ]
        })
        self.tax_template.description = "Other description"
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        with self.assertRaises(Exception):
            wizard.action_update_records()
        # Errors on account update - continuing after that
        wizard.continue_on_errors = True
        wizard.action_update_records()
        self.assertFalse(self.account.reconcile)
        self.assertEqual(self.tax.description, self.tax_template.description)
        self.assertEqual(wizard.rejected_updated_account_number, 1)
        self.assertEqual(wizard.updated_accounts, 0)
        wizard.unlink()
        # Errors on account_creation
        self.account_template.reconcile = False
        new_account_tmpl_2 = self._create_account_tmpl(
            'Test account 3', '444444', self.account_type, self.chart_template,
        )
        wizard = self.wizard_obj.create(self.wizard_vals)
        wizard.action_find_records()
        self.assertEqual(wizard.account_ids.type, 'new')
        new_account_tmpl_2.code = '333333'  # Trick the code for forcing error
        with self.assertRaises(Exception):
            wizard.action_update_records()
        wizard.continue_on_errors = True
        wizard.action_update_records()
        self.assertEqual(wizard.rejected_new_account_number, 1)
        self.assertEqual(wizard.new_accounts, 0)
        wizard.unlink()
