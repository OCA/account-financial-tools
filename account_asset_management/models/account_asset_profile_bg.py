# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountBgAssetProfile(models.Model):
    _name = 'account.bg.asset.profile'
    _description = 'Tax Asset profile'
    _order = 'name'

    name = fields.Char(string='Name', size=64, required=True, index=True)
    note = fields.Text()
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True,
        default=lambda self: self._default_company_id())
    parent_id = fields.Many2one(
        comodel_name='account.asset',
        string='Parent Asset',
        domain=[('type', '=', 'view')])
    category_id = fields.Many2one(
        comodel_name='account.asset.category',
        string='Asset Category')
    method = fields.Selection(
        selection=lambda self: self._selection_method(),
        string='Computation Method',
        required=True,
        help="Choose the method to use to compute the depreciation lines.\n"
             " * Percentage: Calculated on basis of: "
             "Depreciation Base * Percentage per Year. "
             "Depreciation Base = Purchase Value - Salvage Value.\n",
        default='percentage')
    method_percentage = fields.Float(
        string='Percentage per Year',
        help="The Percentage per year needed to depreciate your asset",
        default=15.0)
    active = fields.Boolean(default=True)

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('account.asset')

    @api.model
    def _selection_method(self):
        return[
            ('percentage', _('Percentage per Year')),
        ]

