# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import Command, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain


class AccountLoanLine(models.Model):
    _inherit = "account.loan.line"

    loan_type = fields.Selection(
        related="loan_id.loan_type",
    )

    def _invoice_vals(self):
        self.ensure_one()
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "move_type": "in_invoice",
            "partner_id": self.loan_id.partner_id.id,
            "invoice_date": self.date,
            "journal_id": self.loan_id.journal_id.id,
            "company_id": self.loan_id.company_id.id,
            "invoice_line_ids": [
                Command.create(vals) for vals in self._invoice_line_vals()
            ],
        }

    def _add_basic_values_invoice_line(self, vals):
        vals.append(
            {
                "product_id": self.loan_id.product_id.id,
                "name": self.loan_id.product_id.name,
                "quantity": 1,
                "price_unit": self.principal_amount,
                "account_id": self.loan_id.short_term_loan_account_id.id,
            }
        )
        return vals

    def _add_interests_values_invoice_line(self, vals):
        vals.append(
            {
                "product_id": self.loan_id.interests_product_id.id,
                "name": self.loan_id.interests_product_id.name,
                "quantity": 1,
                "price_unit": self.interests_amount,
                "account_id": self.loan_id.interest_expenses_account_id.id,
            }
        )
        return vals

    def _invoice_line_vals(self):
        vals = list()
        vals = self._add_basic_values_invoice_line(vals)
        vals = self._add_interests_values_invoice_line(vals)
        return vals

    def _generate_invoice(self):
        """
        Computes invoices of leases
        :return: list of account.move generated
        """
        res = []
        for record in self:
            if not record.move_ids:
                if record.loan_id.line_ids.filtered(
                    lambda r, rec=record: r.date < rec.date and not r.move_ids
                ):
                    raise UserError(self.env._("Some invoices must be created first"))
                invoice = self.env["account.move"].create(record._invoice_vals())
                res.append(invoice.id)
                for line in invoice.invoice_line_ids:
                    line.tax_ids = line._get_computed_taxes()
                invoice.flush_recordset()
                invoice.filtered(
                    lambda m: m.currency_id.round(m.amount_total) < 0
                ).action_switch_move_type()
                if record.loan_id.post_invoice:
                    invoice.action_post()
                if (
                    record.long_term_loan_account_id
                    and record.long_term_principal_amount != 0
                ):
                    move = self.env["account.move"].create(
                        record._long_term_move_vals()
                    )
                    if record.loan_id.post_invoice:
                        move.action_post()
                    res.append(move.id)
        return res

    def _long_term_move_vals(self):
        return {
            "loan_line_id": self.id,
            "loan_id": self.loan_id.id,
            "date": self.date,
            "ref": self.name,
            "journal_id": self.loan_id.long_term_journal_id.id
            or self.loan_id.journal_id.id,
            "line_ids": [
                Command.create(vals) for vals in self._get_long_term_move_line_vals()
            ],
        }

    def view_account_values(self):
        """Shows the invoice if it is a leasing or the move if it is a loan"""
        self.ensure_one()
        if self.loan_type == "leasing":
            return self.view_account_invoices()
        return super().view_account_values()

    def _generate_account_entry(self):
        self.ensure_one()
        if self.loan_type == "leasing":
            return self._generate_invoice()
        return super()._generate_account_entry()

    def view_account_invoices(self):
        self.ensure_one()
        result = self.env["ir.actions.act_window"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        result["context"] = {
            "default_loan_line_id": self.id,
            "default_loan_id": self.loan_id.id,
        }
        result["domain"] = Domain("loan_line_id", "=", self.id)
        if len(self.move_ids) == 1:
            res = self.env.ref("account.view_move_form", False)
            result["views"] = [(res and res.id or False, "form")]
            result["res_id"] = self.move_ids.id
        return result
