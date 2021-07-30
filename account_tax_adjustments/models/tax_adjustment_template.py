# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api

import logging
_logger = logging.getLogger(__name__)


class TaxAdjustmentTemplate(models.Model):
    _name = 'tax.adjustment.template'
    _inherit = ['mail.activity.mixin', 'mail.thread']
    _description = 'Template for tax adjustment'

    @api.model
    def _company_get(self):
        return self.env['res.company']._company_default_get(object='tax.adjustment.template')

    name = fields.Char(
        string='Name of template',
        required=True
    )
    reason = fields.Char(
        string='Justification',
        required=True
    )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        required=True,
        domain=[('type', '=', 'general')])
    choice_period_type = fields.Selection([
            ('month', 'Fiscal month'),
            ('year', 'Fiscal year'),
        ],
        string='Type period',
        default='month'
    )
    company_id = fields.Many2one(
        'res.company',
        required=True,
        change_default=True,
        default=_company_get,
    )
    debit_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Debit account',
        required=True,
        domain=[('deprecated', '=', False)]
    )
    credit_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Credit account',
        required=True,
        domain=[('deprecated', '=', False)]
    )
    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Adjustment Tax',
        ondelete='restrict',
        domain=[('type_tax_use', '=', 'none'), ('tax_adjustment', '=', True)],
        required=True
    )
    adjustment_type = fields.Selection([
        ('debit', 'Applied on debit journal item'),
        ('credit', 'Applied on credit journal item')],
        string="Adjustment Type",
        required=True
    )