# Copyright 2020 ForgeFlow, S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo.addons.stock_account.models.account_move import AccountMove


def post_load_hook():
    def new_stock_account_prepare_anglo_saxon_out_lines_vals(self):
        lines_vals_list = []
        for move in self:
            # Make the loop multi-company safe when accessing models like product.product
            move = move.with_company(move.company_id)

            if (
                not move.is_sale_document(include_receipts=True)
                or not move.company_id.anglo_saxon_accounting
            ):
                continue

            for line in move.invoice_line_ids:

                # Filter out lines being not eligible for COGS.
                # FIRST HOOK STARTS
                if not line._eligible_for_cogs():
                    continue
                # FIRST HOOK ENDS

                # Retrieve accounts needed to generate the COGS.
                accounts = line.product_id.product_tmpl_id.get_product_accounts(
                    fiscal_pos=move.fiscal_position_id
                )
                debit_interim_account = accounts["stock_output"]
                credit_expense_account = (
                    accounts["expense"] or move.journal_id.default_account_id
                )
                if not debit_interim_account or not credit_expense_account:
                    continue
                # Add interim account line.
                # SECOND HOOK STARTS
                interim_account_line_vals = self._prepare_interim_account_line_vals(
                    line, move, debit_interim_account
                )
                lines_vals_list.append(interim_account_line_vals)
                expense_account_line_vals = self._prepare_expense_account_line_vals(
                    line, move, credit_expense_account
                )
                lines_vals_list.append(expense_account_line_vals)
                # SECOND HOOK ENDS
        return lines_vals_list

    if not hasattr(
        AccountMove, "stock_account_prepare_anglo_saxon_out_lines_vals_original"
    ):
        AccountMove.stock_account_prepare_anglo_saxon_out_lines_vals_original = (
            AccountMove._stock_account_prepare_anglo_saxon_out_lines_vals
        )

    AccountMove._stock_account_prepare_anglo_saxon_out_lines_vals = (
        new_stock_account_prepare_anglo_saxon_out_lines_vals
    )
