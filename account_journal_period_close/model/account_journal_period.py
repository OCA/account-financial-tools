# -*- coding: utf-8 -*-
# Copyright 2014 Acsone SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models, _
from openerp.exceptions import ValidationError


class AccountJournalPeriod(models.Model):
    _inherit = 'account.journal.period'
    _order = "type,name"

    type = fields.Char(
        'journal_id.type',
        string='Journal Type',
        store=True,
        readonly=True,
    )

    _sql_constraints = [
        ('journal_period_uniq', 'unique(period_id, journal_id)',
         'You can not add same journal in the same period twice.'),
    ]

    @api.multi
    def _check(self):
        return True

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def action_done(self):
        for journal_period in self:
            draft_move_ids = self.env['account.move'].search_count([
                ('period_id', '=', journal_period.period_id.id),
                ('state', '=', "draft"),
                ('journal_id', '=', journal_period.journal_id.id)])
            if draft_move_ids:
                raise ValidationError(_(
                    'In order to close a journal,'
                    ' you must first post related'
                    ' journal entries.'))
        return self.write({'state': 'done'})

    @api.model
    def create(self, values):
        if 'name' not in values:
            if values.get('period_id') and values.get('journal_id'):
                journal = self.env['account.journal'].browse(
                    values['journal_id'])
                period = self.env['account.period'].browse(
                    values['period_id'])
                values.update({'name': (journal.code or journal.name)+':' +
                               (period.name or '')})
        return super(AccountJournalPeriod, self).create(values)
