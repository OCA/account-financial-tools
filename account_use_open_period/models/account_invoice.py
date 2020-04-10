# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields, _


class AccountInvoice(models.Model):
        _inherit = "account.invoice"

        @api.multi
        def action_move_create(self):
                for inv in self:
                        if inv.type in ['in_invoice', 'in_refund'] and inv.company_id.period_lock_date and (inv.date_invoice != False and inv.date_invoice <= inv.company_id.period_lock_date):
                                inv.date, last_day_date = inv.company_id._check_last_lock_date()
                return super(AccountInvoice, self).action_move_create()
