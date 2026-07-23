# Copyright 2025 (APSL - Nagarro) Bernat Obrador
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PayrollImportMapping(models.Model):
    _name = "payroll.import.mapping"
    _description = "Payroll Import Mapping"

    name = fields.Char("Mapping Name", required=True)
    journal_id = fields.Many2one("account.journal", string="Journal", required=True)
    id_column = fields.Char(
        "ID Column",
        required=True,
        help="""Name of the column in the Excel file that contains
        VAT/ID/Pasport numbers to map with the contact.
        It uses the identification_id or passport_id field of the employee.""",
    )
    mapping_line_ids = fields.Many2many(
        "payroll.import.mapping.line", string="Column Mappings"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )


class PayrollImportMappingLine(models.Model):
    _name = "payroll.import.mapping.line"
    _description = "Mapping of Excel columns to accounting accounts"

    column_name = fields.Char("Excel Column Name", required=True)
    account_id = fields.Many2one("account.account", string="Account", required=True)
    move_type = fields.Selection(
        [("debit", ("Debit")), ("credit", ("Credit"))], required=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
