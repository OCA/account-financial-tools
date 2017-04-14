# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FinancialEdit(models.TransientModel):
    _name = 'financial.edit'

    name = fields.Char()

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True,
    )
    amount = fields.Monetary(
        string=u"Document amount",
        required=True,
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
        # required=True
    )
    date_maturity = fields.Date(
        required=True,
    )
    note = fields.Text(
        string="Change reason",
        required=True,
    )

    @api.model
    def default_get(self, fields):
        res = super(FinancialEdit, self).default_get(fields)
        active_id = self.env.context.get('active_id')
        if (self.env.context.get('active_model') == 'financial.move' and
                active_id):
            fm = self.env['financial.move'].browse(active_id)
            res['currency_id'] = fm.currency_id.id
            res['amount'] = fm.amount
            res['amount_discount'] = fm.amount_discount
            res['date_maturity'] = fm.date_maturity
        return res

    def doit(self):
        for wizard in self:
            active_id = self._context['active_id']
            if (self.env.context.get('active_model') == 'financial.move' and
                    active_id):
                fm = self.env['financial.move'].browse(active_id)
                fm.write({
                    'currency_id': wizard.currency_id.id,
                    'amount': wizard.amount,
                    'amount_discount': wizard.amount_discount,
                    'date_maturity': wizard.date_maturity,
                    'note': wizard.note,
                })
        return {'type': 'ir.actions.act_window_close', }
