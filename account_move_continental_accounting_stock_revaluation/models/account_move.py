from odoo import _, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    allow_move_with_valuation_cancelation = fields.Boolean(
        compute="_compute_allow_move_with_valuation_cancelation"
    )

    def _compute_allow_move_with_valuation_cancelation(self):
        with_valuation = self.sudo().filtered("line_ids.stock_valuation_layer_ids")
        continental_accounting = with_valuation.filtered(
            lambda it: not it.company_id.anglo_saxon_accounting
        )
        (
            self - with_valuation - continental_accounting
        ).allow_move_with_valuation_cancelation = False
        for rec in with_valuation:
            rec._compute_show_reset_to_draft_button()
            rec.allow_move_with_valuation_cancelation = rec.show_reset_to_draft_button
            rec.show_reset_to_draft_button = False

    def button_draft(self):
        """
        Overrides the `button_draft` method to include stock valuation adjustment.

        This method first calls the parent class's `button_draft` method to perform
        the standard draft button functionality. After that, it calls the
        `adjust_stock_valuation` method to adjust the stock valuation accordingly.

        Returns:
            The result of the parent class's `button_draft` method.
        """
        res = super().button_draft()
        self.adjust_stock_valuation()
        return res

    def adjust_stock_valuation(self):
        """
        Adjusts the stock valuation for products in real-time valuation category when
        resetting to draft bill.

        This method filters stock valuation layers (SVLs) associated with purchase
        documents that are not using Anglo-Saxon accounting.
        For each filtered SVL, it creates a revaluation entry to adjust the stock
        valuation.

        The revaluation entry includes:
        - Product ID
        - Company ID
        - Added value (negative of the SVL value)
        - Reason for adjustment
        - Account ID (stock input account)
        - Date of the SVL creation

        If any revaluation entries are created, they are validated.

        Returns:
            None
        """
        svl_reevaluation_vals = []
        for svl in (
            self.filtered(
                lambda it: not it.company_id.anglo_saxon_accounting
                and it.is_purchase_document(include_receipts=True)
            )
            .sudo()
            .mapped("line_ids.stock_valuation_layer_ids")
        ):
            product = svl.product_id
            product_property_valuation = product.categ_id.property_valuation
            if product_property_valuation == "real_time":
                svl_reevaluation_val = {
                    "product_id": product.id,
                    "company_id": svl.company_id.id,
                }
                svl_reevaluation_val["added_value"] = -svl.value
                account_move = svl.account_move_line_id.move_id
                svl_reevaluation_val["reason"] = _(
                    "Adjust stock valuation when reseting to draft bill: %s",
                    account_move.name,
                )
                accounts = product.product_tmpl_id.get_product_accounts(
                    fiscal_pos=account_move.fiscal_position_id
                )
                account = accounts.get("stock_input")
                svl_reevaluation_val["account_id"] = account.id
                svl_reevaluation_val["date"] = svl.create_date
                svl_reevaluation_vals.append(svl_reevaluation_val)
        if svl_reevaluation_vals:
            SVLReevaluation = self.env["stock.valuation.layer.revaluation"].sudo()
            svl_revaluations = SVLReevaluation.create(svl_reevaluation_vals)
            for svl_revaluation in svl_revaluations:
                svl_revaluation.action_validate_revaluation()
