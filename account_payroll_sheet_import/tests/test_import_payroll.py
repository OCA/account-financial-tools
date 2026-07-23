import base64
import os

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestPayrollImport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.account = cls.env["account.account"].create(
            {
                "name": "Test Account",
                "code": "2241",
            }
        )
        cls.credit_account = cls.env["account.account"].create(
            {
                "name": "Credit Account",
                "code": "2242",
            }
        )

        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Test Payroll Journal",
                "type": "general",
                "code": "TPJ",
                "company_id": cls.env.company.id,
                "default_account_id": cls.account.id,
            }
        )

        cls.mapping_line = cls.env["payroll.import.mapping.line"].create(
            {
                "column_name": "PAYROLL",
                "account_id": cls.account.id,
                "move_type": "debit",
                "company_id": cls.env.company.id,
            }
        )

        cls.mapping_line_credit = cls.env["payroll.import.mapping.line"].create(
            {
                "column_name": "COUNTERPART",
                "account_id": cls.credit_account.id,
                "move_type": "credit",
                "company_id": cls.env.company.id,
            }
        )

        cls.mapping = cls.env["payroll.import.mapping"].create(
            {
                "name": "Test Mapping",
                "journal_id": cls.journal.id,
                "id_column": "VAT",
                "mapping_line_ids": [
                    (6, 0, [cls.mapping_line.id, cls.mapping_line_credit.id])
                ],
                "company_id": cls.env.company.id,
            }
        )

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test",
                "vat": "001-1234567-8",
                "company_id": cls.env.company.id,
            }
        )

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test",
                "identification_id": "001-1234567-8",
                "work_contact_id": cls.partner.id,
                "company_id": cls.env.company.id,
            }
        )

    def _load_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), "files", filename)
        with open(path, "rb") as f:
            return base64.b64encode(f.read())

    def test_import_with_valid_partner(self):
        file_data = self._load_file("test_payroll_1.xlsx")

        wizard = self.env["payroll.import.wizard"].create(
            {
                "file": file_data,
                "filename": "test_payroll.xlsx",
                "mapping_id": self.mapping.id,
            }
        )

        action = wizard.action_import_payroll()
        move = self.env["account.move"].browse(action["res_id"])

        self.assertTrue(move)
        self.assertEqual(len(move.line_ids), 2)
        self.assertEqual(move.line_ids[0].debit, 10000)
        self.assertEqual(move.line_ids[0].account_id, self.account)
        self.assertEqual(move.line_ids[1].credit, 10000)
        self.assertEqual(move.line_ids[1].account_id, self.credit_account)

    def test_missing_partner_detected(self):
        file_data = self._load_file("test_payroll_2.xlsx")

        wizard = self.env["payroll.import.wizard"].create(
            {
                "file": file_data,
                "filename": "test_payroll.xlsx",
                "mapping_id": self.mapping.id,
            }
        )

        action = wizard.action_import_payroll()
        self.assertIn("001-1234567-9", action["context"]["default_missing_ids"])

    def test_invalid_extension(self):
        file_data = self._load_file("test_payroll_1.xlsx")
        wizard = self.env["payroll.import.wizard"].create(
            {
                "file": file_data,
                "filename": "test_payroll.txt",
                "mapping_id": self.mapping.id,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.action_import_payroll()

        self.assertIn("Only Excel files are supported.", str(e.exception))

    def test_missing_column(self):
        file_data = self._load_file("test_payroll_1.xlsx")

        missing_mapping_line = self.env["payroll.import.mapping.line"].create(
            {
                "column_name": "NON_EXISTENT",
                "account_id": self.account.id,
                "move_type": "debit",
                "company_id": self.env.company.id,
            }
        )

        mapping = self.env["payroll.import.mapping"].create(
            {
                "name": "Mapping Missing Column",
                "journal_id": self.journal.id,
                "id_column": "VAT",
                "mapping_line_ids": [(6, 0, [missing_mapping_line.id])],
                "company_id": self.env.company.id,
            }
        )

        wizard = self.env["payroll.import.wizard"].create(
            {
                "file": file_data,
                "filename": "test_payroll_1.xlsx",
                "mapping_id": mapping.id,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.action_import_payroll()

        self.assertIn("mapped Excel columns are missing", str(e.exception))

    def test_invalid_vat_column(self):
        file_data = self._load_file("test_payroll_1.xlsx")

        mapping = self.env["payroll.import.mapping"].create(
            {
                "name": "Mapping Invalid VAT Column",
                "journal_id": self.journal.id,
                "id_column": "NON_EXISTENT_VAT_COLUMN",
                "mapping_line_ids": [
                    (6, 0, [self.mapping_line.id, self.mapping_line_credit.id])
                ],
                "company_id": self.env.company.id,
            }
        )

        wizard = self.env["payroll.import.wizard"].create(
            {
                "file": file_data,
                "filename": "test_payroll_1.xlsx",
                "mapping_id": mapping.id,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.action_import_payroll()

        self.assertIn("VAT/ID column", str(e.exception))

    def test_balance_mismatch(self):
        file_data = self._load_file("test_payroll_1.xlsx")

        mapping = self.env["payroll.import.mapping"].create(
            {
                "name": "Mapping Balance mismatch",
                "journal_id": self.journal.id,
                "id_column": "VAT",
                "mapping_line_ids": [(6, 0, [self.mapping_line.id])],
                "company_id": self.env.company.id,
            }
        )

        wizard = self.env["payroll.import.wizard"].create(
            {
                "file": file_data,
                "filename": "test_payroll_1.xlsx",
                "mapping_id": mapping.id,
            }
        )

        with self.assertRaises(ValidationError) as e:
            wizard.action_import_payroll()

        self.assertIn("Balance mismatch for employee", str(e.exception))
