# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_register_payment(self):
        """Register Payment from Server Action, add netting context"""
        res = super().action_register_payment()
        active_domain = self.env.context.get("active_domain")
        for domain in active_domain:
            if (
                isinstance(domain, list)
                and domain[0] == "move_type"
                and "in_invoice" in domain[2]
                and "out_invoice" in domain[2]
            ):
                res["context"]["netting"] = True
        return res
