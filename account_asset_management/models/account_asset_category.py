# -*- coding: utf-8 -*-
# Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2009-2017 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import api, fields, models, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class AccountAssetCategory(models.Model):
    _name = 'account.asset.category'
    _description = 'Asset category'
    _order = 'name'

    name = fields.Char('Name', size=64, required=True, index=1)
    note = fields.Text()
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        domain=[('type', '!=', 'view'),
                ('state', 'not in', ('close', 'cancelled'))])
    account_asset_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
        string='Asset Account', required=True)
    account_depreciation_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
        string='Depreciation Account', required=True)
    account_expense_depreciation_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
        string='Depr. Expense Account', required=True)
    account_plus_value_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
        string='Plus-Value Account')
    account_min_value_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
        string='Min-Value Account')
    account_residual_value_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('type', '=', 'other')],
        string='Residual Value Account')
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal', required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True,
        default=lambda self: self._default_company_id())
    parent_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Parent Asset',
        domain=[('type', '=', 'view')])
    method = fields.Selection(
        selection=lambda self: self._selection_method(),
        string='Computation Method',
        required=True,
        help="Choose the method to use to compute the depreciation lines.\n"
             "  * Linear: Calculated on basis of: "
             "Depreciation Base / Number of Depreciations. "
             "Depreciation Base = Purchase Value - Salvage Value.\n"
             "  * Linear-Limit: Linear up to Salvage Value. "
             "Depreciation Base = Purchase Value.\n"
             "  * Degressive: Calculated on basis of: "
             "Residual Value * Degressive Factor.\n"
             "  * Degressive-Linear (only for Time Method = Year): "
             "Degressive becomes linear when the annual linear "
             "depreciation exceeds the annual degressive depreciation.\n"
             "   * Degressive-Limit: Degressive up to Salvage Value. "
             "The Depreciation Base is equal to the asset value.",
        default='linear')
    method_number = fields.Integer(
        string='Number of Years',
        help="The number of years needed to depreciate your asset",
        default=5)
    method_period = fields.Selection(
        selection=[('month', 'Month'),
                   ('quarter', 'Quarter'),
                   ('year', 'Year')],
        string='Period Length', required=True,
        default='year',
        help="Period length for the depreciation accounting entries")
    method_progress_factor = fields.Float(
        string='Degressive Factor', default=0.3)
    method_time = fields.Selection(
        selection=lambda self: self._selection_method_time(),
        string='Time Method', required=True,
        default='year',
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n")
    prorata = fields.Boolean(
        string='Prorata Temporis',
        help="Indicates that the first depreciation entry for this asset "
             "has to be done from the depreciation start date instead of "
             "the first day of the fiscal year.")
    open_asset = fields.Boolean(
        string='Skip Draft State',
        help="Check this if you want to automatically confirm the assets "
             "of this category when created by invoices.")
    active = fields.Boolean(default=True)

    @api.model
    @api.model
    def _default_company_id(self):
        return self.env[
            'res.company']._company_default_get('account.asset.asset')

    @api.model
    def _selection_method(self):
        return[
            ('linear', _('Linear')),
            ('linear-limit', _('Linear up to Salvage Value')),
            ('degressive', _('Degressive')),
            ('degr-linear', _('Degressive-Linear')),
            ('degr-limit', _('Degressive  up to Salvage Value')),
        ]

    @api.model
    def _selection_method_time(self):
        """
        Install the 'account_asset_management_method_number_end' to enable the
        'Number' and 'End' Time Methods.
        """
        return [
            ('year', _('Number of Years')),
        ]

    @api.multi
    @api.constrains('method')
    def _check_method(self):
        for categ in self:
            if categ.method == 'degr-linear' and categ.method_time != 'year':
                raise UserError(
                    _("Degressive-Linear is only supported for Time Method = "
                      "Year."))

    @api.onchange('method_time')
    def _onchange_method_time(self):
        if self.method_time != 'year':
            self.prorata = True

    @api.model
    def create(self, vals):
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        profile = super(AccountAssetCategory, self).create(vals)
        acc_id = vals.get('account_asset_id')
        if acc_id:
            account = self.env['account.account'].browse(acc_id)
            if not account.asset_category_id:
                account.write({'asset_category_id': profile.id})
        return profile

    @api.multi
    def write(self, vals):
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        super(AccountAssetCategory, self).write(vals)
        for profile in self:
            acc_id = vals.get('account_asset_id')
            if acc_id:
                account = self.env['account.account'].browse(acc_id)
                if not account.asset_category_id:
                    account.write({'asset_category_id': profile.id})
        return True
