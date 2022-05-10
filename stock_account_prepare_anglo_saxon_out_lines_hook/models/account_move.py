# Copyright 2020 ForgeFlow S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountMove(models.Model):

    _inherit = "account.move"

    def _prepare_interim_account_line_vals(self, line, move, debit_interim_account):
        # Compute accounting fields.
        sign = -1 if move.move_type == "out_refund" else 1
        price_unit = line._stock_account_get_anglo_saxon_price_unit()
        balance = sign * line.quantity * price_unit
        return {
            "name": line.name[:64],
            "move_id": move.id,
            "partner_id": move.commercial_partner_id.id,
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
        sign = -1 if move.move_type == "out_refund" else 1
        price_unit = line._stock_account_get_anglo_saxon_price_unit()
        balance = sign * line.quantity * price_unit
        return {
            "name": line.name[:64],
            "move_id": move.id,
            "partner_id": move.commercial_partner_id.id,
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
