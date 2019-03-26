# Copyright 2019 Ecosoft Co., Ltd (http://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import api, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        move = super().create(vals)
        move._update_document_id()
        return move

    @api.multi
    def write(self, vals):
        res = super().write(vals)
        for move in self:
            move._update_document_id()
        return res

    @api.multi
    def _update_document_id(self):
        if not self.document_id:
            # Invoice
            invoice = self.line_ids.mapped('invoice_id')
            if invoice:
                invoice.ensure_one()
                self.document_id = invoice
                return
            # Payment
            payment = self.line_ids.mapped('payment_id')
            if payment:
                payment.ensure_one()
                self.document_id = payment
                return
            # Bank Statement
            statement = self.line_ids.mapped('statement_id')
            if statement:
                statement.ensure_one()
                self.document_id = statement
                return
