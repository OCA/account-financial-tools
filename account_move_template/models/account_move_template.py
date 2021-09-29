# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class AccountMoveTemplate(models.Model):
    _name = 'account.move.template'
    _inherit = ['account.document.template',
                # 'mail.activity.mixin',  TODO:  uncomment for saas-15
                'mail.thread']

    @api.model
    def _company_get(self):
        return self.env['res.company']._company_default_get(
            object='account.move.template'
        )

    company_id = fields.Many2one(
        'res.company',
        required=True,
        change_default=True,
        default=_company_get,
    )
    template_line_ids = fields.One2many(
        'account.move.template.line',
        inverse_name='template_id',
    )

    @api.multi
    def action_run_template(self):
        self.ensure_one()
        action = self.env.ref(
            'account_move_template.action_wizard_select_template').read()[0]
        action.update({'context': {'default_template_id': self.id}})
        return action


class AccountMoveTemplateLine(models.Model):
    _name = 'account.move.template.line'
    _inherit = 'account.document.template.line'

    journal_id = fields.Many2one('account.journal', required=True)
    account_id = fields.Many2one('account.account', required=True, ondelete="cascade", copy=False)
    move_line_type = fields.Selection([
                                        ('cr', 'Credit'),
                                        ('dr', 'Debit'),
                                        ('dc', 'Auto'),
                                        ], required=True)
    analytic_account_id = fields.Many2one('account.analytic.account', ondelete="cascade")
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Default Analytic tags')

    template_id = fields.Many2one('account.move.template')

    _sql_constraints = [
        ('sequence_template_uniq', 'unique (template_id,sequence)',
         'The sequence of the line must be unique per template !')
    ]

    def action_dublicate(self):
        for record in self:
            account_id = self.env['account.account'].search([('code', 'ilike', record.account_id.code[:3]),
                                                             ('company_id', '=', record.template_id.company_id.id)])
            account_ids = record.template_id.template_line_ids.\
                filtered(lambda r: r.move_line_type == record.move_line_type).mapped('account_id').ids
            account_id = account_id.filtered(lambda r: r.id not in account_ids)
            # _logger.info("LINES %s:%s" % (account_ids, account_id))

            if account_id:
                # _logger.info("LINES %s:%s" % (account_ids, account_id.filtered(lambda r: r.id not in account_ids)))
                new = record.copy(default={'account_id': account_id[0].id, 'sequence': record.sequence + 1})
                new.update({'template_id': record.template_id.id})
                # record.template_id.template_line_ids.new(new)
                # _logger.info("LINES NEW %s:%s" % (new, record.template_id.template_line_ids))
        return True

    def action_close(self):
        for record in self:
            if record.type == 'computed':
                lines = set([])
                for line in record.template_id.template_line_ids[:-1].mapped('python_code'):
                    operators = line.split('+')
                    operators = [l.replace('L(','').replace(')','')
                                 for l in filter(lambda l: l.startswith('L('), operators)]
                    for row in operators:
                        lines.update([row])
                record.python_code = "+".join(["L(%s)" % x for x in record.template_id.template_line_ids.
                                              filtered(lambda r: r.sequence not in list(lines))[:-1].mapped('sequence')])
