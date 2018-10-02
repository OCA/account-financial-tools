# -*- coding: utf-8 -*-
# Copyright 2014 Acsone SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class AccountPeriod(models.Model):
    _inherit = 'account.period'

    journal_period_ids = fields.One2many(
        'account.journal.period',
        'period_id',
        'Journal states',
    )

    @api.multi
    def add_all_journals(self):
        for rec in self:
            journal_period_obj = self.env['account.journal.period']
            journal_period_ids = journal_period_obj\
                .search([('period_id', '=', rec.id)])
            journal_list = []
            for journal_period in journal_period_ids:
                journal_list.append(journal_period.journal_id.id)
            journal_ids = self.env['account.journal'].search([
                ('id', 'not in', journal_list)])
            for journal_id in journal_ids:
                journal_period_obj.create({
                    'period_id': rec.id,
                    'journal_id': journal_id,
                    'state': rec.state})
