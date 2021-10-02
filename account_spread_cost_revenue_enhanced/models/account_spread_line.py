# Copyright 2021 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountInvoiceSpreadLine(models.Model):
    _inherit = "account.spread.line"

    def _prepare_move(self):
        """Create with move_type, i.e., in_invoice instead of normal entry"""
        res = super()._prepare_move()
        if self.spread_id.create_move_type != "entry":
            invoice_line = res.pop("line_ids")[0][2]
            res["name"] = False
            res["move_type"] = self.spread_id.create_move_type
            res["partner_id"] = self.spread_id.invoice_line_id.partner_id.id
            invoice_line["price_unit"] = abs(self.amount)
            res["invoice_line_ids"] = [(0, 0, invoice_line)]
        return res
