# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import io
from collections import defaultdict

import pandas as pd

from odoo import fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain


class PayrollImportWizard(models.TransientModel):
    _name = "payroll.import.wizard"
    _description = "Payroll Excel Importer"

    file = fields.Binary("Excel File", required=True)
    filename = fields.Char()
    mapping_id = fields.Many2one(
        "payroll.import.mapping", string="Column Mapping", required=True
    )

    def get_account_map(self):
        """Builds account mapping filtered by company"""
        account_map = defaultdict(list)
        for line in self.mapping_id.mapping_line_ids:
            if line.company_id == self.mapping_id.company_id:
                account_map[line.column_name].append((line.account_id, line.move_type))
        return account_map

    def get_partner(self, vat):
        """Searches for employee by VAT and return the asociated partner."""
        employee = self.env["hr.employee"].search(
            Domain.OR(
                [
                    Domain("identification_id", "=", vat),
                    Domain("passport_id", "=", vat),
                ]
            ),
            limit=1,
        )
        return employee.work_contact_id if employee else None

    def show_mismatch_error(self, move_lines, partner, vat, total_debit, total_credit):
        partner_lines = [
            line[2] for line in move_lines if line[2].get("partner_id") == partner.id
        ]
        line_rows = ["\n{:<10} | {:<10} | {}".format("Debit", "Credit", "Description")]
        line_rows.append("-" * 50)
        for line in partner_lines:
            line_rows.append(
                "{:<10.2f} | {:<10.2f} | {}".format(
                    line["debit"], line["credit"], line["name"]
                )
            )
        line_table = "\n".join(line_rows)

        raise ValidationError(
            self.env._(
                "Balance mismatch for employee %(employee)s (%(vat)s):\n"
                "  Total Debit: %(debit).2f / Total Credit: %(credit).2f\n\n"
                "%(lines)s",
                employee=partner.name,
                vat=vat,
                debit=total_debit,
                credit=total_credit,
                lines=line_table,
            )
        )

    def check_columns(self, df, account_map):
        missing_columns = [col for col in account_map if col not in df.columns]
        if missing_columns:
            raise ValidationError(
                self.env._(
                    "The following mapped Excel columns are missing "
                    "from the uploaded file:\n- %(columns)s",
                    columns="\n- ".join(missing_columns),
                )
            )

        if self.mapping_id.id_column not in df.columns:
            raise ValidationError(
                self.env._(
                    "The VAT/ID column '%(column)s' specified in the mapping "
                    "is missing from the uploaded file.",
                    column=self.mapping_id.id_column,
                )
            )

    def build_move_lines(self, df, account_map):
        move_lines = []
        not_found = []

        for __, row in df.iterrows():
            total_debit = 0
            total_credit = 0

            vat_raw = row.get(self.mapping_id.id_column)
            if pd.isna(vat_raw):
                continue

            vat = str(vat_raw).strip()
            partner = self.get_partner(vat)
            if not partner:
                not_found.append(vat)
                continue

            for col_name, raw_value in row.items():
                if col_name not in account_map or pd.isna(raw_value):
                    continue

                amount = float(raw_value)
                if not amount:
                    continue

                for account, move_type in account_map[col_name]:
                    effective_move_type = (
                        "debit"
                        if (move_type == "debit" and amount > 0)
                        or (move_type == "credit" and amount < 0)
                        else "credit"
                    )

                    move_lines.append(
                        (
                            0,
                            0,
                            {
                                "name": col_name,
                                "account_id": account.id,
                                "partner_id": partner.id,
                                "debit": (
                                    abs(amount) if effective_move_type == "debit" else 0
                                ),
                                "credit": (
                                    abs(amount)
                                    if effective_move_type == "credit"
                                    else 0
                                ),
                                "company_id": self.mapping_id.company_id.id,
                            },
                        )
                    )

                    if effective_move_type == "debit":
                        total_debit += abs(amount)
                    else:
                        total_credit += abs(amount)

            if round(total_debit, 2) != round(total_credit, 2):
                self.show_mismatch_error(
                    move_lines, partner, vat, total_debit, total_credit
                )

        return move_lines, not_found

    def action_import_payroll(self):
        if not self.file:
            raise ValidationError(self.env._("Please upload a file."))

        if not self.filename.endswith((".xlsx", ".xls")):
            raise ValidationError(self.env._("Only Excel files are supported."))

        data = base64.b64decode(self.file)
        df = df = pd.read_excel(io.BytesIO(data))

        account_map = self.get_account_map()
        self.check_columns(df, account_map)
        move_lines, not_found = self.build_move_lines(df, account_map)

        if not_found:
            return {
                "type": "ir.actions.act_window",
                "res_model": "missing.partner.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_missing_ids": "\n".join(not_found)},
            }
        if not move_lines:
            raise ValidationError(self.env._("No valid data found in the file."))

        move = self.env["account.move"].create(
            {
                "journal_id": self.mapping_id.journal_id.id,
                "ref": f"{self.filename} - {fields.Date.today()}",
                "line_ids": move_lines,
                "company_id": self.mapping_id.company_id.id,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": move.id,
            "target": "current",
        }
