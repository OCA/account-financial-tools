# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetProfile(models.Model):
    _name = 'account.asset.profile'
    _description = 'Asset profile'
    _order = 'name'

    name = fields.Char(string='Name', size=64, required=True, index=True)
    note = fields.Text()
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account')
    account_asset_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Asset Account', required=True)
    account_depreciation_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Depreciation Account', required=True)
    account_expense_depreciation_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Depr. Expense Account', required=True)
    account_plus_value_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Plus-Value Account')
    account_min_value_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Min-Value Account')
    account_residual_value_id = fields.Many2one(
        comodel_name='account.account',
        domain=[('deprecated', '=', False)],
        string='Residual Value Account')
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        domain=[('type', '=', 'general')],
        string='Journal', required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True,
        default=lambda self: self._default_company_id())
    parent_id = fields.Many2one(
        comodel_name='account.asset',
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
        selection=lambda self: self._selection_method_period(),
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
             "of this profile when created by invoices.")
    asset_product_item = fields.Boolean(
        string='Create an asset by product item',
        help="By default during the validation of an invoice, an asset "
             "is created by invoice line as long as an accounting entry is "
             "created by invoice line. "
             "With this setting, an accounting entry will be created by "
             "product item. So, there will be an asset by product item.")
    active = fields.Boolean(default=True)

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('account.asset')

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
    def _selection_method_period(self):
        return [
            ('month', _('Month')),
            ('quarter', _('Quarter')),
            ('year', _('Year')),
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
        for profile in self:
            if profile.method == 'degr-linear' and \
                    profile.method_time != 'year':
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
        profile = super().create(vals)
        acc_id = vals.get('account_asset_id')
        if acc_id:
            account = self.env['account.account'].browse(acc_id)
            if not account.asset_profile_id:
                account.write({'asset_profile_id': profile.id})
        return profile

    @api.multi
    def write(self, vals):
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        res = super().write(vals)
        # TODO last profile in self is defined as default on the related
        # account. must be improved.
        account = self.env['account.account'].browse(
            vals.get('account_asset_id'))
        if self and account and not account.asset_profile_id:
            account.write({'asset_profile_id': self[-1].id})
        return res
