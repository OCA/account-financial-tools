# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_due = fields.Float(string="Credit Due", compute="_compute_credit_due")
    credit_left = fields.Float(string="Credit Left", compute="_compute_credit_due")
    credit_overload = fields.Boolean(string="Overload Credit limit", compute="_compute_credit_due")
    parent_id = fields.Many2one(related="partner_id.parent_id", string='Related Company')

    @api.multi
    def _compute_credit_due(self):
        for record in self:
            if record.partner_id:
                ctx = dict(self._context, lang=record.partner_id.lang)
                due_left = sum([x.value_amount for x in record.partner_id.property_payment_term_id.mapped("line_ids") if x.value == "fixed"])
                partner = record.partner_id.parent_id and record.partner_id.parent_id or record.partner_id
                partner_id = partner.id
                credit_due = sum([x.balance_due for x in self.env["credit.control.line"].search([('partner_id', '=', partner_id), ('date', '=', fields.Datetime.now())])])
                #_logger.info("Opended invoices %s:%s:%s" % (partner.total_opened_invoice, credit_due, due_left))
                if credit_due > 0.0:
                    record.credit_left = -credit_due
                    record.credit_due = credit_due
                    record.credit_overload = True
                    record.credit_left = due_left - partner.total_opened_invoice
                    record.partner_id.sale_warn = 'block'
                    record.partner_id.sale_warn_msg = 'The client of this order has exceeded its credit limit or has unpaid obligations. Contact an authorized person.'
                elif due_left > 0.0:
                    record.credit_left = due_left - partner.total_opened_invoice
                    record.credit_due = credit_due
                    record.credit_overload = record.credit_left < 0.0
                    record.partner_id.sale_warn = 'block'
                    record.partner_id.sale_warn_msg = 'The client of this order has exceeded its credit limit or has unpaid obligations. Contact an authorized person.'
                else:
                    record.credit_due = 0.0
                    record.credit_left = 0.0
                    record.credit_overload = False
            else:
                record.credit_due = 0.0
                record.credit_left = 0.0
                record.credit_overload = False

    @api.multi
    def _action_credit_control(self):
        self.ensure_one()
        ctx = dict(self._context, default_partner_id=self.partner_id.id)
        credit = self.env["credit.control.run"].sudo()
        credit_run = credit.create({'date': max(self.date_order or self.validity_date, fields.Datetime.now())})
        credit_run.with_context(ctx).generate_credit_lines()
        if not credit_run.line_ids:
            credit_run.unlink()

    @api.multi
    def _credit_limit(self):
        self.ensure_one()
        if self.credit_due == 0.0 and self.credit_left == 0.0:
            return False
        if self.credit_due > 0.0:
            return True
        if (self.credit_left - self.amount_total) < 0.0:
            return True
        return False

    @api.multi
    def _action_confirm(self):
        ret = super(SaleOrder, self)._action_confirm()
        self.sudo()._action_credit_control()
        return ret

    @api.one
    def _send_message_credt_control(self):
        if self.state != "cancel" and (self.credit_overload or self._credit_limit()):
            user_ids_to_attach_as_chat_followers = [self.partner_id.id]
            if self.partner_id.payment_responsible_id:
                user_ids_to_attach_as_chat_followers.append(self.partner_id.payment_responsible_id.id)
            if self.partner_id.payment_responsible_id and self.partner_id.payment_responsible_id.parent_id:
                user_ids_to_attach_as_chat_followers.append(self.partner_id.payment_responsible_id.parent_id.id)
            self.message_post(
                subject=_("Credit control: (%s)") % 'has exceeded its credit limit or has unpaid obligations',
                body=_("The client of this order (%s) has exceeded its credit limit (%s) or has unpaid obligations (%s).") % (
                    self.name,
                    self.credit_left,
                    self.credit_due,
                ),
                partner_ids=user_ids_to_attach_as_chat_followers,
                )

    #@api.model
    #def create(self, values):
    #    res = super(SaleOrder, self).create(values)
    #    #res._send_message_credt_control()
    #    return res

    #@api.multi
    #def write(self, values):
    #    res = super(SaleOrder, self).write(values)
    #    #self._send_message_credt_control()
    #    return res
