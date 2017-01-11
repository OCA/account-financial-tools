# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, fields, exceptions, models, _


class AccountAssetProfile(models.Model):
    _name = 'account.asset.profile'
    _description = 'Asset category'
    _order = 'name'

    @api.model
    def _get_method(self):
        return[
            ('linear', _('Linear')),
            ('degressive', _('Degressive')),
            ('degr-linear', _('Degressive-Linear'))
        ]

    @api.model
    def _get_method_time(self):
        return [
            ('year', _('Number of Years')),
            # ('number', _('Number of Depreciations')),
            # ('end', _('Ending Date'))
        ]

    @api.model
    def _get_method_period(self):
        return [
            ('month', 'Month'),
            ('quarter', 'Quarter'),
            ('year', 'Year'),
        ]

    name = fields.Char('Name', size=64, required=True, index=1)
    note = fields.Text('Note')
    account_analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic account',
        domain=[('type', '!=', 'view'),
                ('state', 'not in', ('close', 'cancelled'))])
    account_asset_id = fields.Many2one(
        'account.account', 'Asset Account', required=True)
    account_depreciation_id = fields.Many2one(
        'account.account', 'Depreciation Account', required=True)
    account_expense_depreciation_id = fields.Many2one(
        'account.account', 'Depr. Expense Account', required=True)
    account_plus_value_id = fields.Many2one(
        'account.account', 'Plus-Value Account')
    account_min_value_id = fields.Many2one(
        'account.account', 'Min-Value Account')
    account_residual_value_id = fields.Many2one(
        'account.account', 'Residual Value Account')
    journal_id = fields.Many2one(
        'account.journal', 'Journal', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda self: self._get_company())
    parent_id = fields.Many2one(
        'account.asset',
        'Parent Asset',
        domain=[('type', '=', 'view')])
    method = fields.Selection(
        selection=lambda self: self._get_method(), string='Computation Method',
        required=True,
        help="Choose the method to use to compute "
             "the amount of depreciation lines.\n"
             "  * Linear: Calculated on basis of: "
             "Gross Value / Number of Depreciations\n"
             "  * Degressive: Calculated on basis of: "
             "Residual Value * Degressive Factor"
             "  * Degressive-Linear (only for Time Method = Year): "
             "Degressive becomes linear when the annual linear "
             "depreciation exceeds the annual degressive depreciation",
        default='linear')
    method_number = fields.Integer(
        'Number of Years',
        help="The number of years needed to depreciate your asset",
        default=5)
    method_period = fields.Selection(
        selection=lambda self: self._get_method_period(),
        string='Period Length', required=True,
        help="Period length for the depreciation accounting entries",
        default='year')
    method_progress_factor = fields.Float('Degressive Factor', default=0.3)
    method_time = fields.Selection(
        selection=lambda self: self._get_method_time(),
        string='Time Method', required=True,
        default='year',
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             # "  * Number of Depreciations: Fix the number of "
             # "depreciation lines and the time between 2 depreciations.\n"
             # "  * Ending Date: Choose the time between 2 depreciations "
             # "and the date the depreciations won't go beyond."
    )
    prorata = fields.Boolean(
        'Prorata Temporis',
        help="Indicates that the first depreciation entry for this asset "
             "has to be done from the depreciation start date instead of "
             "the first day of the fiscal year.")
    open_asset = fields.Boolean(
        'Skip Draft State',
        help="Check this if you want to automatically confirm the assets "
        "of this category when created by invoices.")
    active = fields.Boolean('Active', default=True)

    @api.model
    def _get_company(self):
        return self.env['res.company']._company_default_get(
            'account.asset.profile')

    @api.constrains
    @api.multi
    def _check_method(self):
        for asset in self:
            if asset.method == 'degr-linear' and asset.method_time != 'year':
                raise exceptions.ValidationEroor(
                    _("Degressive-Linear is only supported for Time Method = "
                      "Year."))

    @api.onchange('method_time')
    def onchange_method_time(self):
        if self.method_time != 'year':
            self.prorata = True

    @api.model
    def create(self, vals):
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        group = super(AccountAssetProfile, self).create(vals)
        acc_obj = self.env['account.account']
        acc_id = vals.get('account_asset_id')
        if acc_id:
            account = acc_obj.browse(acc_id)
            if not account.asset_profile_id:
                account.write({'asset_profile_id': group.id})
        return group

    @api.multi
    def write(self, vals):
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        res = super(AccountAssetProfile, self).write(vals)
        acc_obj = self.env['account.account']
        for profile in self:
            acc_id = vals.get('account_asset_id')
            if acc_id:
                account = acc_obj.browse(acc_id)
                if not account.asset_profile_id:
                    account.write({'asset_profile_id': profile.id})
        return res
