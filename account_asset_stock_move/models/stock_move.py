# Copyright 2021 Ecosoft Co., Ltd. <http://ecosoft.co.th>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from odoo.exceptions import UserError
from odoo.tests.common import Form


class StockMove(models.Model):
    _inherit = "stock.move"

    def _generate_valuation_lines_data(
        self,
        partner_id,
        qty,
        debit_value,
        credit_value,
        debit_account_id,
        credit_account_id,
        description,
    ):
        """
        Assign Account's Asset Profile (if any)
        """
        rslt = super()._generate_valuation_lines_data(
            partner_id,
            qty,
            debit_value,
            credit_value,
            debit_account_id,
            credit_account_id,
            description,
        )
        for entry in rslt.values():
            account = self.env["account.account"].browse(entry["account_id"])
            entry["asset_profile_id"] = account.asset_profile_id.id
        return rslt

    def _create_account_move_line(
        self,
        credit_account_id,
        debit_account_id,
        journal_id,
        qty,
        description,
        svl_id,
        cost,
    ):
        """
        Create Asset (if asset_profile_id exists)
        """
        res = super()._create_account_move_line(
            credit_account_id,
            debit_account_id,
            journal_id,
            qty,
            description,
            svl_id,
            cost,
        )
        for move in self.env["account.move"].search([("stock_move_id", "=", self.id)]):
            for aml in move.line_ids.filtered("asset_profile_id"):
                vals = move._prepare_asset_vals(aml)
                if not aml.name:
                    raise UserError(
                        _("Asset name must be set in the label of the line.")
                    )
                asset_form = Form(
                    self.env["account.asset"]
                    .with_company(move.company_id)
                    .with_context(create_asset_from_move_line=True, move_id=move.id)
                )
                for key, val in vals.items():
                    setattr(asset_form, key, val)
                asset = asset_form.save()
                asset.analytic_tag_ids = aml.analytic_tag_ids
                aml.with_context(allow_asset=True).asset_id = asset.id
            refs = [
                "<a href=# data-oe-model=account.asset data-oe-id=%s>%s</a>"
                % tuple(name_get)
                for name_get in move.line_ids.filtered(
                    "asset_profile_id"
                ).asset_id.name_get()
            ]
            if refs:
                message = _("This journal entry created the asset(s): %s") % ", ".join(
                    refs
                )
                move.message_post(body=message)
        return res
