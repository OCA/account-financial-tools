# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

import logging
_logger = logging.getLogger(__name__)


class WizardRebuildAllLinesAccountMoves(models.TransientModel):
    _inherit = "wizard.rebuild.lines.account.moves"

    mrp_production_id = fields.Many2one('mrp.production', 'Manufacture production')

    def _get_lines(self, begin_date, end_date, company_id, rebuild_id=False):
        res = super(WizardRebuildAllLinesAccountMoves, self)._get_lines(begin_date, end_date, company_id)
        begin_date = fields.Datetime.to_string(begin_date)
        end_date = fields.Datetime.to_string(end_date)

        # manufacture productions
        productions = self.env['mrp.production'].search([('date_finished', '>=', begin_date),
                                                         ('date_finished', '<=', end_date),
                                                         ('company_id', '=', company_id.id),
                                                         ('state', '=', 'done')])

        for production in productions:
            res.append((0, 0, {
                'date': productions.date_finished,
                'mrp_production_id': productions.id,
                'sequence': 2,
            }))
            if rebuild_id:
                res[-1][2]['rebuild_id'] = rebuild_id

        return res

    def _execute_rebuld(self):
        if self.mrp_production_id:
            self.mrp_production_id.rebuild_account_move()
            self.write({'ready': True})
        return super(WizardRebuildAllLinesAccountMoves, self)._execute_rebuld()