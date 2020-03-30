# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [('name', operator, name)]
        payment = self.search(domain + args, limit=limit)
        return payment.name_get()

    @api.multi
    def name_get(self):
        """Return special label when showing fields in move line"""
        res = []
        for record in self:
            res.append((record.id, "%s" % (record.payment_id.name)))
        return res
