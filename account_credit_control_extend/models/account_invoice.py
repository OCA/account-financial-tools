# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    credit_due = fields.Float(string="Credit Due", compute="_compute_credit_due")

    @api.one
    def _compute_credit_due(self):
        for record in self:
            record.credit_due = sum([x.balance_due for x in self.env["credit.control.line"].search([('invoice_id', '=', record.id)])])

