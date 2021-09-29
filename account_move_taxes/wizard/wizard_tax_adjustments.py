# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class TaxAdjustments(models.TransientModel):
    _inherit = 'tax.adjustments.wizard'

    vattype = fields.Many2one("account.vattype", "Vat type doc")
    narration_id = fields.Many2one('base.comment.template', string='Narration Template')

    @api.multi
    def _create_move(self):
        adjustment_type = self.env.context.get('adjustment_type', (self.amount > 0.0 and 'debit' or 'credit'))
        debit_vals = {
            'name': self.reason,
            'debit': abs(self.amount),
            'credit': 0.0,
            'account_id': self.debit_account_id.id,
            'tax_line_id': adjustment_type == 'debit' and self.tax_id.id or False,
        }
        credit_vals = {
            'name': self.reason,
            'debit': 0.0,
            'credit': abs(self.amount),
            'account_id': self.credit_account_id.id,
            'tax_line_id': adjustment_type == 'credit' and self.tax_id.id or False,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'state': 'draft',
            'vattype': self.vattype,
            'narration_id': self.narration_id.id,
            'applicability': 'declar',
            'work_with_taxes': True,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.post()
        return move.id
