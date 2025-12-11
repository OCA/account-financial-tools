from odoo.tests import tagged

from odoo.addons.account_chart_update.tests.common import TestAccountChartUpdateCommon


@tagged("-at_install", "post_install")
class AccountChartUpdateWizardTest(TestAccountChartUpdateCommon):
    def test_wizard(self):
        """Test the wizard code_digits logics."""
        wizard = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        self.assertEqual(wizard.company_id, self.company)
        self.assertEqual(wizard.chart_template, "generic_coa")
        # Verify code_digits is 6 when opening due to default number
        wizard._onchage_chart_template()
        self.assertEqual(self.company.account_code_digits, 0)
        self.assertEqual(wizard.code_digits, 6)
        # Change the code_digits to 10
        wizard.code_digits = 10
        wizard.action_find_records()
        # Company code_digits are not changed till the accounts are modified
        self.assertEqual(self.company.account_code_digits, 0)
        wizard.action_update_records()
        # When the accounts are updated, it change
        self.assertEqual(self.company.account_code_digits, 10)

        wizard2 = self.wizard_obj.with_company(self.company).create(self.wizard_vals)
        self.assertEqual(wizard2.company_id, self.company)
        self.assertEqual(wizard2.chart_template, "generic_coa")
        # Verify that code_digits is 10 when opening
        wizard2._onchage_chart_template()
        self.assertEqual(wizard2.code_digits, 10)
