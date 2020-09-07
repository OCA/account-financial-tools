# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_interim_account_line_vals(self, line, move, debit_interim_account):
        # Compute accounting fields.
        sign = -1 if move.type == "out_refund" else 1
        price_unit = line._stock_account_get_anglo_saxon_price_unit()
        balance = sign * line.quantity * price_unit
        return {
            "name": line.name[:64],
            "move_id": move.id,
            "product_id": line.product_id.id,
            "product_uom_id": line.product_uom_id.id,
            "quantity": line.quantity,
            "price_unit": price_unit,
            "debit": balance < 0.0 and -balance or 0.0,
            "credit": balance > 0.0 and balance or 0.0,
            "account_id": debit_interim_account.id,
            "exclude_from_invoice_tab": True,
            "is_anglo_saxon_line": True,
        }

    def _prepare_expense_account_line_vals(self, line, move, credit_expense_account):
        # Compute accounting fields.
        sign = -1 if move.type == "out_refund" else 1
        price_unit = line._stock_account_get_anglo_saxon_price_unit()
        balance = sign * line.quantity * price_unit
        return {
            "name": line.name[:64],
            "move_id": move.id,
            "product_id": line.product_id.id,
            "product_uom_id": line.product_uom_id.id,
            "quantity": line.quantity,
            "price_unit": -price_unit,
            "debit": balance > 0.0 and balance or 0.0,
            "credit": balance < 0.0 and -balance or 0.0,
            "account_id": credit_expense_account.id,
            "analytic_account_id": line.analytic_account_id.id,
            "analytic_tag_ids": [(6, 0, line.analytic_tag_ids.ids)],
            "exclude_from_invoice_tab": True,
            "is_anglo_saxon_line": True,
        }

    def _stock_account_prepare_anglo_saxon_out_lines_vals(self):
        """
        Copy of Odoo original method to include vital information to extend it
        """
        lines_vals_list = []
        for move in self:
            if (
                not move.is_sale_document(include_receipts=True)
                or not move.company_id.anglo_saxon_accounting
            ):
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                if (
                    line.product_id.type != "product"
                    or line.product_id.valuation != "real_time"
                ):
                    continue

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.with_context(
                    force_company=line.company_id.id
                ).get_product_accounts(fiscal_pos=move.fiscal_position_id)
                debit_interim_account = accounts["stock_output"]
                credit_expense_account = accounts["expense"]
                if not debit_interim_account or not credit_expense_account:
                    continue
                interim_account_line_vals = self._prepare_interim_account_line_vals(
                    line, move, debit_interim_account
                )
                lines_vals_list.append(interim_account_line_vals)
                expense_account_line_vals = self._prepare_expense_account_line_vals(
                    line, move, credit_expense_account
                )
                lines_vals_list.append(expense_account_line_vals)
        return lines_vals_list
