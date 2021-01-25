# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class OpeningAccountMoveWizard(models.TransientModel):
    _inherit = 'account.opening'

    @api.model
    def default_get(self, fields):
        res = super(OpeningAccountMoveWizard, self).default_get(fields)
        company = self.env['res.company'].browse(self._context.get('default_company_id', False))
        if company:
            opening_move_id = company.opening_move_id
            self.write({
                'company_id': company and company.id or False,
                'opening_move_id': opening_move_id.id,
                'currency_id': opening_move_id.currency_id.id,
                'opening_move_line_ids': [(6, False, opening_move_id.line_ids.ids)],
                'journal_id': opening_move_id.journal_id.id,
                'date': opening_move_id.date,
            })
        return res
