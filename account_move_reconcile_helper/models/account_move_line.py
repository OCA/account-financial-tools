# -*- coding: utf-8 -*-
# Copyright 2015 ACSONE SA/NV (<http://acsone.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, api, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    @api.depends('reconcile_id', 'reconcile_partial_id', 'line_partial_ids')
    def _compute_get_reconcile(self):
        for rec in self:
            if rec.reconcile_id:
                rec.reconcile_ref = rec.reconcile_id.name
            elif rec.reconcile_partial_id:
                rec.reconcile_ref = "P/" + rec.reconcile_partial_id.name

    reconcile_ref = fields.Char(
        compute='_compute_get_reconcile',
        string='Reconcile Ref',
        store=True,
    )

    credit_debit_balance = fields.Float(
        compute='_compute_debit_credit_balance',
        string='Balance',
        store=True,
    )

    @api.multi
    @api.depends('debit', 'credit')
    def _compute_debit_credit_balance(self):
        for rec in self:
            rec.credit_debit_balance = rec.debit - rec.credit
