# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    followup_line_id = fields.Many2one(
        comodel_name='account_followup.followup.line',
        string='Follow-up Level',
        ondelete='restrict',  # restrict deletion of the followup line
    )
    followup_date = fields.Date(
        string='Latest Follow-up',
        select=True,
    )
    followup_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner Follow-up',
    )
    result = fields.Float(
        string="Balance",  # 'balance' field is not the same
        compute='_compute_result',
    )

    @api.multi
    def _compute_result(self):
        for aml in self:
            aml.result = aml.debit - aml.credit
