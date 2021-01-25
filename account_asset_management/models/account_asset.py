# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import calendar
import datetime
from datetime import datetime as dt
from datetime import date
from dateutil.relativedelta import relativedelta
import logging
from sys import exc_info
from traceback import format_exception

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from odoo.osv import expression
from functools import reduce

_logger = logging.getLogger(__name__)


class DummyFy(object):
    def __init__(self, *args, **argv):
        for key, arg in argv.items():
            setattr(self, key, arg)


class AccountAsset(models.Model):
    _name = 'account.asset'
    _description = 'Asset'
    _inherits = {'product.product': 'product_id', }
    _order = 'date_start desc, code, name'
    _parent_store = True

    account_move_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='asset_id',
        string='Entries', readonly=True, copy=False)
    purchase_line_ids = fields.One2many(
        comodel_name='purchase.order.line',
        compute='_compute_purchase_line_ids'
    )
    move_line_ids = fields.One2many(
        comodel_name='stock.move.line',
        inverse_name='asset_id',
        string='Operations', readonly=True, copy=False)
    move_line_id = fields.Many2one(
        comodel_name='stock.move.line',
        string="Operaraton", copy=False)
    move_line_check = fields.Boolean(
        compute='_compute_move_line_check',
        string='Has accounting entries')
    name = fields.Char(
        string='Asset Name', size=64, required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char(
        string='Reference', size=32, readonly=True,
        states={'draft': [('readonly', False)]})
    product_id = fields.Many2one('product.product', string='Base on Product', required=True, ondelete='cascade')
    categ_id = fields.Many2one(
        'product.category', 'Internal Category', related="product_id.product_tmpl_id.categ_id")
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    lot_name = fields.Char('Lot/Serial Number')
    quant_ids = fields.One2many('stock.quant', string='Quants', related="lot_id.quant_ids", readonly=True)
    location_ids = fields.One2many('stock.location', string="Locatons", compute="_compute_locations_ids")

    product_asset_ids = fields.Many2many("product.template", relation="asset_product_tmpl_rel", column1="asset_id", column2="product_tmpl_id", string="Linked to asset")
    diff_purchase_value = fields.Float('Cost difference', compute="_compute_diff_purchase_value")
    purchase_value = fields.Float(
        string='Purchase Value', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        help="This amount represent the initial value of the asset."
             "\nThe Depreciation Base is calculated as follows:"
             "\nPurchase Value - Salvage Value.")
    salvage_value = fields.Float(
        string='Salvage Value', digits=dp.get_precision('Account'),
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="The estimated value that an asset will realize upon "
             "its sale at the end of its useful life.\n"
             "This value is used to determine the depreciation amounts.")
    depreciation_base = fields.Float(
        compute='_compute_depreciation_base',
        digits=dp.get_precision('Account'),
        string='Depreciation Base',
        store=True,
        help="This amount represent the depreciation base "
             "of the asset (Purchase Value - Salvage Value.")
    value_residual = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='Residual Value',
        store=True)
    value_depreciated = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='Depreciated Value',
        store=True)
    fy_value_residual = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='End FY Residual Value',
        store=True)
    fy_value_depreciated = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='FY Depreciated Value',
        store=True)
    tax_value_residual = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='Residual Value',
        store=True)
    tax_value_depreciated = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='Depreciated Value',
        store=True)
    tax_fy_value_residual = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='End FY Residual Value',
        store=True)
    tax_fy_value_depreciated = fields.Float(
        compute='_compute_depreciation',
        digits=dp.get_precision('Account'),
        string='FY Depreciated Value',
        store=True)
    fiscal_correction_value = fields.Float(
        string='Fiscal correction Value', digits=dp.get_precision('Account'),
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="This value is used for correction Depreciation Base. \n"
             "If you are have some amount with for fiscal restricts, \n"
             "enter it with minus.")
    note = fields.Text('Note')
    profile_id = fields.Many2one(
        comodel_name='account.asset.profile',
        string='Asset Profile',
        change_default=True, readonly=True,
        states={'draft': [('readonly', False)]})
    tax_profile_id = fields.Many2one(
        comodel_name='account.bg.asset.profile',
        string='Tax Asset Profile',
        change_default=True, readonly=True,
        states={'draft': [('readonly', False)]})
    category_id = fields.Many2one(
        comodel_name='account.asset.category',
        string='Asset Category',
        change_default=True, readonly=True,
        states={'draft': [('readonly', False)]})
    parent_id = fields.Many2one(
        comodel_name='account.asset',
        string='Parent Asset', readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('type', '=', 'view')],
        ondelete='restrict',
        index=True,
    )
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)
    child_ids = fields.One2many(
        comodel_name='account.asset',
        inverse_name='parent_id',
        string='Child Assets')
    date_buy = fields.Date(
        string='Asset Bay Date', readonly=True,
        states={'draft': [('readonly', False)]})
    date_start = fields.Date(
        string='Asset Start Date', readonly=True,
        states={'draft': [('readonly', False)]},
        help="You should manually add depreciation lines "
             "with the depreciations of previous fiscal years "
             "if the Depreciation Start Date is different from the date "
             "for which accounting entries need to be generated.")
    date_remove = fields.Date(string='Asset Removal Date', readonly=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Running'),
            ('close', 'Close'),
            ('removed', 'Removed'),
        ], string='Status', required=True, default='draft', copy=False,
        help="When an asset is created, the status is 'Draft'.\n"
             "If the asset is confirmed, the status goes in 'Running' "
             "and the depreciation lines can be posted "
             "to the accounting.\n"
             "If the last depreciation line is posted, "
             "the asset goes into the 'Close' status.\n"
             "When the removal entries are generated, "
             "the asset goes into the 'Removed' status.")
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Partner', readonly=True,
        states={'draft': [('readonly', False)]})
    method = fields.Selection(
        selection=lambda self: self.env[
            'account.asset.profile']._selection_method(),
        string='Computation Method',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='linear',
        help="Choose the method to use to compute "
             "the amount of depreciation lines.\n"
             "  * Linear: Calculated on basis of: "
             "Gross Value / Number of Depreciations\n"
             "  * Degressive: Calculated on basis of: "
             "Residual Value * Degressive Factor"
             "  * Degressive-Linear (only for Time Method = Year): "
             "Degressive becomes linear when the annual linear "
             "depreciation exceeds the annual degressive depreciation")
    method_number = fields.Integer(
        string='Number of Years', readonly=True,
        states={'draft': [('readonly', False)]}, default=5,
        help="The number of years needed to depreciate your asset")
    method_period = fields.Selection(
        selection=lambda self: self.env[
            'account.asset.profile']._selection_method_period(),
        string='Period Length',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='year',
        help="Period length for the depreciation accounting entries")
    method_end = fields.Date(
        string='Ending Date', readonly=True,
        states={'draft': [('readonly', False)]})
    method_progress_factor = fields.Float(
        string='Degressive Factor', readonly=True,
        states={'draft': [('readonly', False)]}, default=0.3)
    method_time = fields.Selection(
        selection=lambda self: self.env[
            'account.asset.profile']._selection_method_time(),
        string='Time Method',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='year',
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             # "  * Number of Depreciations: Fix the number of "
             # "depreciation lines and the time between 2 depreciations.\n"
             # "  * Ending Date: Choose the time between 2 depreciations "
             # "and the date the depreciations won't go beyond."
    )
    method_tax_time = fields.Selection(selection=lambda self: self.env[
            'account.bg.asset.profile']._selection_method(),
        string='Fiscal Time Method',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='percentage',
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             # "  * Number of Depreciations: Fix the number of "
             # "depreciation lines and the time between 2 depreciations.\n"
             # "  * Ending Date: Choose the time between 2 depreciations "
             # "and the date the depreciations won't go beyond."
        )
    fiscal_method_percentage = fields.Float(related="tax_profile_id.method_percentage",
                                            string="Fiscal Percentage per Year",
                                            store=True)
    prorata = fields.Boolean(
        string='Prorata Temporis', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Indicates that the first depreciation entry for this asset "
             "have to be done from the depreciation start date instead "
             "of the first day of the fiscal year.")
    depreciation_line_ids = fields.One2many(
        comodel_name='account.asset.line',
        inverse_name='asset_id',
        string='Depreciation Lines', copy=False,
        readonly=True, states={'draft': [('readonly', False)]})
    depreciation_bg_line_ids = fields.One2many(
        comodel_name='account.bg.asset.line',
        inverse_name='asset_id',
        string='BG Depreciation Lines', copy=False,
        readonly=True, states={'draft': [('readonly', False)]})
    depreciation_restatement_line_ids = fields.One2many(
        comodel_name='account.asset.restatement.value',
        inverse_name='asset_id',
        string='Restatement Lines', copy=False)
    type = fields.Selection(
        selection=[('view', 'View'),
                   ('normal', 'Normal')],
        string='Type',
        required=True, readonly=True, default='normal',
        states={'draft': [('readonly', False)]})
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company', required=True, readonly=True,
        default=lambda self: self._default_company_id())
    company_currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        store=True, readonly=True)
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('parent_id', '=', False)])

    @api.multi
    def _compute_purchase_line_ids(self):
        for asset in self:
            asset.purchase_line_ids = self.env['purchase.order.line']
            for line in asset.account_move_line_ids:
                if line.product_id == asset.product_id and line.asset_id == asset and line.invoice_id:
                    inv = line.invoice_id
                    for inv_line in inv.invoice_line_ids.filtered(lambda r: r.product_id == asset.product_id):
                        if inv_line.purchase_line_id and inv_line.product_id == asset.product_id:
                            asset.purchase_line_ids |= inv_line.purchase_line_id
                            # _logger.info("ADD %s::%s" % (inv_line.purchase_line_id, asset.purchase_line_ids))

    @api.multi
    def _compute_locations_ids(self):
        for record in self:
            if record.lot_id:
                record.location_ids = False
                for line in record.quant_ids:
                    if line.location_id.usage == 'internal':
                        record.location_ids |= line.location_id

    @api.model
    def _default_company_id(self):
        return self.env['res.company']._company_default_get('account.asset')

    @api.depends('purchase_value', 'diff_purchase_value')
    @api.multi
    def _compute_diff_purchase_value(self):
        for asset in self:
            asset.diff_purchase_value = asset.purchase_value - asset.standard_price

    @api.multi
    def _compute_move_line_check(self):
        for asset in self:
            for line in asset.depreciation_line_ids:
                if line.move_id:
                    asset.move_line_check = True
                    break

    @api.depends('purchase_value', 'salvage_value', 'type', 'method')
    @api.multi
    def _compute_depreciation_base(self):
        for asset in self:
            if asset.type == 'view':
                asset.depreciation_base = 0.0
            elif asset.method in ['linear-limit', 'degr-limit']:
                asset.depreciation_base = asset.purchase_value
            else:
                asset.depreciation_base = \
                    asset.purchase_value - asset.salvage_value
            asset.depreciation_base += asset.depreciation_restatement_line_ids.get_restatement_value(['create'], asset.date_start, '<=', 'depreciation_base')

    @api.multi
    @api.depends('type', 'depreciation_base',
                 'depreciation_line_ids.type',
                 'depreciation_line_ids.amount',
                 'depreciation_line_ids.previous_id',
                 'depreciation_line_ids.init_entry',
                 'depreciation_line_ids.move_check',)
    def _compute_depreciation(self):
        for asset in self:
            if asset.type == 'normal':
                fy_date_start = date.today() + relativedelta(days=1)
                fy = asset.company_id.find_daterange_fy(fy_date_start)
                lines = asset.depreciation_line_ids.filtered(
                    lambda l: l.type in ('depreciate', 'remove') and
                    (l.init_entry or l.move_check))
                value_depreciated = sum([l.amount for l in lines])
                residual = asset.depreciation_base - value_depreciated
                depreciated = value_depreciated
                fy_value_depreciated = sum([l.amount for l in lines if l.line_date >= fy.date_start and l.line_date <= fy.date_end])
                fy_residual = asset.depreciation_base + asset.salvage_value + asset.fiscal_correction_value - fy_value_depreciated
                fy_depreciated = fy_value_depreciated

                lines = asset.depreciation_bg_line_ids.filtered(
                    lambda l: l.type in ('depreciate', 'remove'))
                tax_value_depreciated = sum([l.amount for l in lines if l.line_date <= fy.date_end])
                # _logger.info("DATES %s-%s" % (fy.date_start, fy.date_end))
                tax_residual = asset.depreciation_base - tax_value_depreciated
                tax_depreciated = tax_value_depreciated
                tax_fy_value_depreciated = sum(
                    [l.amount for l in lines if l.line_date >= fy.date_start and l.line_date <= fy.date_end])
                tax_fy_residual = asset.depreciation_base + asset.salvage_value - tax_fy_value_depreciated
                tax_fy_depreciated = tax_fy_value_depreciated

            else:
                residual = 0.0
                depreciated = 0.0
                fy_residual = 0.0
                fy_depreciated = 0.0
                tax_residual = 0.0
                tax_depreciated = 0.0
                tax_fy_residual = 0.0
                tax_fy_depreciated = 0.0
            asset.update({
                'value_residual': residual,
                'value_depreciated': depreciated,
                'fy_value_residual': fy_residual,
                'fy_value_depreciated': fy_depreciated,
                'tax_value_residual': tax_residual,
                'tax_value_depreciated': tax_depreciated,
                'tax_fy_value_residual': tax_fy_residual,
                'tax_fy_value_depreciated': tax_fy_depreciated,
            })

    @api.multi
    @api.constrains('parent_id')
    def _check_recursion(self, parent=None):
        res = super()._check_recursion(parent=parent)
        if not res:
            raise UserError(
                _("Error ! You can not create recursive assets."))
        return res

    @api.multi
    @api.constrains('method', 'method_time')
    def _check_method(self):
        for asset in self:
            if asset.method == 'degr-linear' and asset.method_time not in ['year', 'month']:
                raise UserError(
                    _("Degressive-Linear is only supported for Time Method = "
                      "Year."))

    @api.multi
    @api.constrains('date_start', 'method_end', 'method_time')
    def _check_dates(self):
        for asset in self:
            if asset.method_time == 'end':
                if asset.method_end <= asset.date_start:
                    raise UserError(
                        _("The Start Date must precede the Ending Date."))

    @api.onchange('move_line_id')
    def _onchange_move_line_id(self):
        if self.move_line_id:
            self.lot_id = self.move_line_id.lot_id
            #self.move_line_ids.write({'asset_id': False})
            # for line in self.move_line_id:
            #     line.write({'asset_id': self.id})

    @api.onchange('purchase_value', 'salvage_value', 'date_start', 'method')
    def _onchange_purchase_salvage_value(self):
        if self.method in ['linear-limit', 'degr-limit']:
            self.depreciation_base = self.purchase_value or 0.0
        else:
            purchase_value = self.purchase_value or 0.0
            salvage_value = self.salvage_value or 0.0
            self.depreciation_base = purchase_value - salvage_value
        dl_create_line = self.depreciation_line_ids.filtered(
            lambda r: r.type == 'create')
        if dl_create_line:
            dl_create_line.update({
                'amount': self.depreciation_base,
            })
            if self.date_start != dl_create_line.line_date:
                dl_create_line.update({
                    'line_date': self.date_start
                })
        dl_bg_create_line = self.depreciation_bg_line_ids.filtered(
            lambda r: r.type == 'create')
        if self.fiscal_method_percentage <= 0.0 and dl_bg_create_line:
            dl_bg_create_line.unlink()
            dl_bg_create_line = False

        if dl_bg_create_line:
            dl_bg_create_line.update({
                'amount': self.depreciation_base + self.salvage_value + self.fiscal_correction_value,
            })
            depreciation_start_date = fields.Datetime.from_string(self.date_start)
            depreciation_start_date = depreciation_start_date + relativedelta(months=1, day=1)
            if fields.Datetime.to_string(depreciation_start_date) != dl_bg_create_line.line_date:
                dl_bg_create_line.update({
                    'line_date': fields.Datetime.to_string(depreciation_start_date)
                })

    @api.onchange('profile_id')
    def _onchange_profile_id(self):
        for line in self.depreciation_line_ids.filtered(lambda r: r.type != 'create'):
            if line.move_id:
                raise UserError(
                    _("You cannot change the profile of an asset "
                      "with accounting entries."))
        profile = self.profile_id
        if profile:
            self.update({
                'category_id': profile.category_id,
                'method': profile.method,
                'method_number': profile.method_number,
                'method_time': profile.method_time,
                'method_period': profile.method_period,
                'method_progress_factor': profile.method_progress_factor,
                'prorata': profile.prorata,
                'account_analytic_id': profile.account_analytic_id,
            })

    @api.onchange('tax_profile_id')
    def _onchange_tax_profile_id(self):
        profile = self.tax_profile_id
        if profile:
            self.update({
                'method_tax_time': profile.method,
                'fiscal_method_percentage': profile.method_percentage
            })

    @api.onchange('method_time')
    def _onchange_method_time(self):
        if self.method_time not in ['year', 'month']:
            self.prorata = True
        if self.method_time == 'month':
            self.method_period = 'month'

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == 'view':
            self.update({
                'date_start': False,
                'profile_id': False,
                'purchase_value': False,
                'salvage_value': False,
            })
        if self.depreciation_line_ids:
            self.depreciation_line_ids.unlink()
        if self.depreciation_bg_line_ids:
            self.depreciation_bg_line_ids.unlink()

    @api.model
    def create(self, vals):
        if vals.get('method_time') not in ['year', 'month'] and not vals.get('prorata'):
            vals['prorata'] = True
        if vals.get('type') == 'view':
            vals['date_start'] = False
        asset = super().create(vals)
        if self.env.context.get('create_asset_from_move_line'):
            # Trigger compute of depreciation_base
            asset.salvage_value = 0.0
        if asset.type == 'normal':
            asset._create_first_asset_line()
        if 'move_line_id' in vals:
            asset.move_line_id.asset_id = asset.id
        return asset

    @api.multi
    def write(self, vals):
        if vals.get('method_time'):
            if vals['method_time'] not in ['year', 'month'] and not vals.get('prorata'):
                vals['prorata'] = True
        res = super().write(vals)
        for asset in self:
            asset_type = vals.get('type') or asset.type
            if asset_type == 'view' or \
                    self.env.context.get('asset_validate_from_write'):
                continue
            asset._create_first_asset_line()
            if asset.profile_id.open_asset and \
                    self.env.context.get('create_asset_from_move_line'):
                asset.compute_depreciation_board()
                # extra context to avoid recursion
                asset.with_context(asset_validate_from_write=True).validate()
            if 'move_line_id' in vals:
                asset.move_line_id.asset_id = asset.id
        if 'depreciation_restatement_line_ids' in vals:
            self.recalculate()

        return res

    def _create_first_asset_line(self):
        self.ensure_one()
        if self.depreciation_base and not self.depreciation_line_ids:
            asset_line_obj = self.env['account.asset.line']
            asset_line_value = {
                'amount': self.depreciation_base,
                'asset_id': self.id,
                'name': self._get_depreciation_entry_name(0),
                'line_date': self.date_start,
                'init_entry': True,
                'type': 'create',
            }
            asset_line = asset_line_obj.create(asset_line_value)
            if self.env.context.get('create_asset_from_move_line'):
                asset_line.move_id = self.env.context['move_id']
        elif self.depreciation_base and self.fiscal_method_percentage > 0.0 and not self.depreciation_bg_line_ids:
            depreciation_start_date = fields.Datetime.from_string(self.date_start)
            depreciation_start_date = depreciation_start_date + relativedelta(months=1, day=1)
            asset_line_obj = self.env['account.bg.asset.line']
            asset_line_value = {
                'amount': self.depreciation_base + self.salvage_value + self.fiscal_correction_value,
                'asset_id': self.id,
                'name': self._get_depreciation_entry_name(0),
                'line_date': fields.Datetime.to_string(depreciation_start_date),
                'init_entry': True,
                'type': 'create',
            }
            asset_line_obj.create(asset_line_value)

    @api.multi
    def unlink(self):
        for asset in self:
            if asset.state != 'draft':
                raise UserError(
                    _("You can only delete assets in draft state."))
            if asset.depreciation_line_ids.filtered(
                    lambda r: r.type == 'depreciate' and r.move_check):
                raise UserError(
                    _("You cannot delete an asset that contains "
                      "posted depreciation lines."))
        # remove ling from stock move
        move = self.mapped('move_line_ids')
        move.write({'asset_id': False})
        # update accounting entries linked to lines of type 'create'
        amls = self.with_context(
            allow_asset_removal=True, from_parent_object=True
        ).mapped('account_move_line_ids')
        amls.write({'asset_id': False})
        return super().unlink()

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|',
                      ('code', '=ilike', name + '%'),
                      ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        assets = self.search(domain + args, limit=limit)
        return assets.name_get()

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        for asset in self:
            name = asset.name
            if asset.code:
                name = ' - '.join([asset.code, name])
            result.append((asset.id, name))
        return result

    @api.multi
    def recalculate(self):
        # recalculate and save all restatement data
        restatement_obj = self.env['account.asset.restatement.value']

        if self.type == 'view':
            self.depreciation_base = 0.0
        elif self.method in ['linear-limit', 'degr-limit']:
            self.depreciation_base = self.purchase_value
        else:
            self.depreciation_base = \
                self.purchase_value - self.salvage_value
        self.depreciation_base += restatement_obj.get_restatement_value(['create'], self.date_start, '<=', 'depreciation_base')
        if self.env.context.get("bg_asset_line"):
            dlines = self.depreciation_bg_line_ids
        else:
            dlines = self.depreciation_line_ids
        for dl in dlines.filtered(lambda l: l.type == 'create'):
            dl.with_context(dict(self.env.context, allow_asset_line_update=True)).write({'amount': self.depreciation_base})
        dlines = dlines.filtered(lambda l: l.type == 'depreciate')
        dlines = dlines.sorted(key=lambda l: l.line_date)
        depreciated_value = remaining_value = 0.0

        for i, dl in enumerate(dlines):
            if i == 0:
                depreciation_base = dl.depreciation_base
                depreciation_base += restatement_obj.get_restatement_value(['create'], dl.line_date, '<=',
                                                      'depreciation_base')
                depreciated_value = dl.previous_id \
                    and (depreciation_base - dl.previous_id.remaining_value) \
                    or 0.0
                depreciated_value += restatement_obj.get_restatement_value(['restatement', 'diminution'], dl.line_date,
                                                                            '<=', 'depreciated_value')
                remaining_value = \
                    depreciation_base - depreciated_value - dl.amount
            else:
                depreciated_value += dl.previous_id.amount + restatement_obj.get_restatement_value(['restatement', 'diminution'], dl.line_date,
                                                                            '=', 'depreciated_value')
                remaining_value -= dl.amount
            dl.depreciated_value = depreciated_value
            dl.remaining_value = remaining_value

    @api.multi
    def validate(self):
        for asset in self:
            if asset.type == 'normal' and asset.company_currency_id.is_zero(
                    asset.value_residual):
                asset.state = 'close'
            else:
                # force recalculate base desperation
                asset._compute_depreciation_base()
                asset._create_first_asset_line()
                asset.with_context(dict(self._context, allow_asset_line_update=True))._onchange_purchase_salvage_value()
                asset.state = 'open'
        return True

    @api.multi
    def remove(self):
        self.ensure_one()
        ctx = dict(self.env.context, active_ids=self.ids, active_id=self.id)

        early_removal = False
        if self.method in ['linear-limit', 'degr-limit']:
            if self.value_residual != self.salvage_value:
                early_removal = True
        elif self.value_residual:
            early_removal = True
        if early_removal:
            ctx.update({'early_removal': True})

        return {
            'name': _("Generate Asset Removal entries"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.remove',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
        }

    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def open_entries(self):
        self.ensure_one()
        amls = self.env['account.move.line'].search(
            [('asset_id', '=', self.id)], order='date ASC')
        am_ids = [l.move_id.id for l in amls]
        return {
            'name': _("Journal Entries"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': [('id', 'in', am_ids)],
        }

    @api.multi
    def compute_depreciation_board(self):

        def group_lines(x, y):
            y.update({'amount': x['amount'] + y['amount']})
            return y

        if self.env.context.get("bg_asset_line"):
            line_obj = self.env['account.bg.asset.line']
        else:
            line_obj = self.env['account.asset.line']
        digits = self.env['decimal.precision'].precision_get('Account')

        for asset in self:
            if asset.value_residual == 0.0:
                continue
            if self.env.context.get("bg_asset_line"):
                domain = [
                    ('asset_id', '=', asset.id),
                    ('type', '=', 'depreciate'),
                    ('init_entry', '=', True),
                ]
            else:
                domain = [
                    ('asset_id', '=', asset.id),
                    ('type', '=', 'depreciate'),
                    '|', ('move_check', '=', True), ('init_entry', '=', True)]
            posted_lines = line_obj.search(
                domain, order='line_date desc')
            if posted_lines:
                last_line = posted_lines[0]
            else:
                last_line = line_obj
            _logger.info("POSTED LINES %s:%s" % (last_line, self._context))
            if self.env.context.get("bg_asset_line"):
                domain = [
                    ('asset_id', '=', asset.id),
                    ('type', '=', 'depreciate'),
                    ('init_entry', '=', False),
                ]
            else:
                domain = [
                    ('asset_id', '=', asset.id),
                    ('type', '=', 'depreciate'),
                    ('move_id', '=', False),
                    ('init_entry', '=', False)]
            old_lines = line_obj.search(domain)
            if old_lines:
                if self.env.context.get("bg_asset_line"):
                    raise UserError(
                        _("An asset entered in the tax depreciation plan can only be written off."))
                else:
                    old_lines.unlink()

            table = asset._compute_depreciation_table()
            _logger.info("TABLE %s" % table)
            if not table:
                continue

            # group lines prior to depreciation start period
            depreciation_start_date = fields.Datetime.from_string(
                asset.date_start)
            if self._context.get('bg_asset_line'):
                depreciation_start_date = depreciation_start_date + relativedelta(months=1, day=1)
            lines = table[0]['lines']
            lines1 = []
            lines2 = []
            flag = lines[0]['date'] < depreciation_start_date
            for line in lines:
                if flag:
                    lines1.append(line)
                    if line['date'] >= depreciation_start_date:
                        flag = False
                else:
                    lines2.append(line)
            if lines1:
                lines1 = [reduce(group_lines, lines1)]
                lines1[0]['depreciated_value'] = 0.0
            table[0]['lines'] = lines1 + lines2

            # check table with posted entries and
            # recompute in case of deviation
            depreciated_value_posted = depreciated_value = 0.0
            if posted_lines:
                last_depreciation_date = fields.Datetime.from_string(
                    last_line.line_date)
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_depreciation_date:
                    raise UserError(
                        _("The duration of the asset conflicts with the "
                          "posted depreciation table entry dates."))

                for table_i, entry in enumerate(table):
                    residual_amount_table = \
                        entry['lines'][-1]['remaining_value']
                    if entry['date_start'] <= last_depreciation_date \
                            <= entry['date_stop']:
                        break
                if entry['date_stop'] == last_depreciation_date:
                    table_i += 1
                    line_i = 0
                else:
                    entry = table[table_i]
                    date_min = entry['date_start']
                    for line_i, line in enumerate(entry['lines']):
                        residual_amount_table = line['remaining_value']
                        if date_min <= last_depreciation_date <= line['date']:
                            break
                        date_min = line['date']
                    if line['date'] == last_depreciation_date:
                        line_i += 1
                table_i_start = table_i
                line_i_start = line_i

                # check if residual value corresponds with table
                # and adjust table when needed
                depreciated_value_posted = depreciated_value = \
                    sum([l.amount for l in posted_lines])
                residual_amount = asset.depreciation_base - depreciated_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    # compensate in first depreciation entry
                    # after last posting
                    line = table[table_i_start]['lines'][line_i_start]
                    line['amount'] -= amount_diff

            else:  # no posted lines
                table_i_start = 0
                line_i_start = 0

            seq = len(posted_lines)
            depr_line = last_line
            last_date = table[-1]['lines'][-1]['date']
            depreciated_value = depreciated_value_posted
            for entry in table[table_i_start:]:
                for line in entry['lines'][line_i_start:]:
                    seq += 1
                    name = asset._get_depreciation_entry_name(seq)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        if asset.method in ['linear-limit', 'degr-limit']:
                            depr_max = asset.depreciation_base \
                                - asset.salvage_value
                        else:
                            depr_max = asset.depreciation_base
                        amount = depr_max - depreciated_value
                    else:
                        amount = line['amount']
                    if amount:
                        _logger.info("LINE %s:%s" % (line, name))
                        vals = {
                            'previous_id': depr_line.id,
                            'amount': amount,
                            'asset_id': asset.id,
                            'name': name,
                            'line_date': line['date'].strftime('%Y-%m-%d'),
                            'init_entry': entry['init'],
                        }
                        depr_line = line_obj.create(vals)
                        depreciated_value += amount
                        _logger.info("LINE NEW %s:%s" % (line_obj,depr_line))
                    else:
                        seq -= 1
                line_i_start = 0
            asset.recalculate()
        return True

    def _get_fy_duration(self, fy_id, option='days'):
        """
        Returns fiscal year duration.
        @param option:
        - days: duration in days
        - months: duration in months,
                  a started month is counted as a full month
        - years: duration in calendar years, considering also leap years
        """
        fy = self.env['date.range'].browse(fy_id)
        fy_date_start = fields.Datetime.from_string(fy.date_start)
        fy_date_stop = fields.Datetime.from_string(fy.date_end)
        days = (fy_date_stop - fy_date_start).days + 1
        months = (fy_date_stop.year - fy_date_start.year) * 12  \
            + (fy_date_stop.month - fy_date_start.month) + 1
        if option == 'days':
            return days
        elif option == 'months':
            return months
        elif option == 'years':
            year = fy_date_start.year
            cnt = fy_date_stop.year - fy_date_start.year + 1
            for i in range(cnt):
                cy_days = calendar.isleap(year) and 366 or 365
                if i == 0:  # first year
                    if fy_date_stop.year == year:
                        duration = (fy_date_stop - fy_date_start).days + 1
                    else:
                        duration = (
                            dt(year, 12, 31) - fy_date_start).days + 1
                    factor = float(duration) / cy_days
                elif i == cnt - 1:  # last year
                    duration = (
                        fy_date_stop - dt(year, 1, 1)).days + 1
                    factor += float(duration) / cy_days
                else:
                    factor += 1.0
                year += 1
            return factor

    def _get_fy_duration_factor(self, entry, firstyear):
        """
        localization: override this method to change the logic used to
        calculate the impact of extended/shortened fiscal years
        """
        duration_factor = 1.0
        fy_id = entry['fy_id']
        if self.prorata:
            if firstyear:
                depreciation_date_start = fields.Datetime.from_string(
                    self.date_start)
                fy_date_stop = entry['date_stop']
                first_fy_asset_days = \
                    (fy_date_stop - depreciation_date_start).days + 1
                if fy_id:
                    first_fy_duration = self._get_fy_duration(
                        fy_id, option='days')
                    first_fy_year_factor = self._get_fy_duration(
                        fy_id, option='years')
                    duration_factor = \
                        float(first_fy_asset_days) / first_fy_duration \
                        * first_fy_year_factor
                else:
                    first_fy_duration = \
                        calendar.isleap(entry['date_start'].year) \
                        and 366 or 365
                    duration_factor = \
                        float(first_fy_asset_days) / first_fy_duration
            elif fy_id:
                duration_factor = self._get_fy_duration(
                    fy_id, option='years')
        elif fy_id:
            fy_months = self._get_fy_duration(
                fy_id, option='months')
            duration_factor = float(fy_months) / 12
        return duration_factor

    def _get_depreciation_start_date(self, fy):
        """
        In case of 'Linear': the first month is counted as a full month
        if the fiscal year starts in the middle of a month.
        """
        if self.prorata:
            depreciation_start_date = fields.Datetime.from_string(
                self.date_start)
            if self._context.get('bg_asset_line'):
                depreciation_start_date = depreciation_start_date + relativedelta(months=1, day=1)
        else:
            fy_date_start = fields.Datetime.from_string(fy.date_start)
            depreciation_start_date = dt(
                fy_date_start.year, fy_date_start.month, 1)
        return depreciation_start_date

    def _get_depreciation_stop_date(self, depreciation_start_date):
        method_time = self.method_time

        if self._context.get('bg_asset_line'):
            method_time = self.method_tax_time

        if method_time == 'year':
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=self.method_number, days=-1)
        elif method_time == 'month':
            (month, year) = (self.method_number % 12, self.method_number // 12)
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=year, days=-1)
            depreciation_stop_date = depreciation_stop_date + \
                relativedelta(months=month, days=-1)
        elif method_time == 'percentage':
            percentage_month = (100/self.fiscal_method_percentage)*12
            (month, year) = (percentage_month % 12, percentage_month // 12)
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=year, days=-1) +\
                relativedelta(months=month, days=-1)
        elif method_time == 'number':
            if self.method_period == 'month':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=self.method_number, days=-1)
            elif self.method_period == 'quarter':
                m = [x for x in [3, 6, 9, 12]
                     if x >= depreciation_start_date.month][0]
                first_line_date = depreciation_start_date \
                    + relativedelta(month=m, day=31)
                months = self.method_number * 3
                depreciation_stop_date = first_line_date \
                    + relativedelta(months=months - 1, days=-1)
            elif self.method_period == 'year':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(years=self.method_number, days=-1)
        elif method_time == 'end':
            depreciation_stop_date = fields.Datetime.from_string(
                self.method_end)
        return depreciation_stop_date

    def _get_first_period_amount(self, table, entry, depreciation_start_date,
                                 line_dates):
        """
        Return prorata amount for Time Method 'Year' in case of
        'Prorata Temporis'
        """
        amount = entry.get('period_amount')
        method_time = self.method_time

        if self._context.get('bg_asset_line'):
            method_time = self.method_tax_time
        if self.prorata and method_time in ['year', 'month']:
            dates = [x for x in line_dates if x <= entry['date_stop']]
            full_periods = len(dates) - 1
            amount = entry['fy_amount'] - amount * full_periods
        return amount

    def _compute_year_amount(self, residual_amount):
        """
        Localization: override this method to change the degressive-linear
        calculation logic according to local legislation.
        """
        method_time = self.method_time

        if self._context.get('bg_asset_line'):
            method_time = self.method_tax_time

        if method_time not in ['year', 'month', 'percentage']:
            raise UserError(
                _("The '_compute_year_amount' method is only intended for "
                  "Time Method 'Number of Years."))
        koef = 1
        if method_time == 'month':
            koef = 12
        if method_time == 'percentage':
            year_amount_linear = self.depreciation_base * (self.fiscal_method_percentage/100)
        else:
            year_amount_linear = self.depreciation_base / (method_time * koef)

        if self.method == 'linear':
            return year_amount_linear
        if self.method == 'linear-limit':
            if (residual_amount - year_amount_linear) < self.salvage_value:
                return residual_amount - self.salvage_value
            else:
                return year_amount_linear
        year_amount_degressive = residual_amount * \
            self.method_progress_factor
        if self.method == 'degressive':
            return year_amount_degressive
        if self.method == 'degr-linear':
            if year_amount_linear > year_amount_degressive:
                return min(year_amount_linear, residual_amount)
            else:
                return min(year_amount_degressive, residual_amount)
        if self.method == 'degr-limit':
            if (residual_amount - year_amount_degressive) < self.salvage_value:
                return residual_amount - self.salvage_value
            else:
                return year_amount_degressive
        else:
            raise UserError(
                _("Illegal value %s in asset.method.") % self.method)

    def _compute_line_dates(self, table, start_date, stop_date):
        """
        The posting dates of the accounting entries depend on the
        chosen 'Period Length' as follows:
        - month: last day of the month
        - quarter: last of the quarter
        - year: last day of the fiscal year

        Override this method if another posting date logic is required.
        """
        line_dates = []

        if self.method_period == 'month':
            line_date = start_date + relativedelta(day=31)
        if self.method_period == 'quarter':
            m = [x for x in [3, 6, 9, 12] if x >= start_date.month][0]
            line_date = start_date + relativedelta(month=m, day=31)
        elif self.method_period == 'year':
            line_date = table[0]['date_stop']

        i = 1
        while line_date < stop_date:
            line_dates.append(line_date)
            if self.method_period == 'month':
                line_date = line_date + relativedelta(months=1, day=31)
            elif self.method_period == 'quarter':
                line_date = line_date + relativedelta(months=3, day=31)
            elif self.method_period == 'year':
                line_date = table[i]['date_stop']
                i += 1

        # last entry
        method_time = self.method_time

        if self._context.get('bg_asset_line'):
            method_time = self.method_tax_time

        if not (method_time == 'number' and
                len(line_dates) == self.method_number):
            line_dates.append(line_date)

        return line_dates

    def _compute_depreciation_table_lines(self, table, depreciation_start_date,
                                          depreciation_stop_date, line_dates):

        digits = self.env['decimal.precision'].precision_get('Account')
        asset_sign = 1 if self.depreciation_base >= 0 else -1
        i_max = len(table) - 1
        remaining_value = self.depreciation_base
        depreciated_value = 0.0

        for i, entry in enumerate(table):

            lines = []
            fy_amount_check = 0.0
            fy_amount = entry['fy_amount']
            li_max = len(line_dates) - 1
            for li, line_date in enumerate(line_dates):

                if round(remaining_value, digits) == 0.0:
                    break

                if (line_date > min(entry['date_stop'],
                                    depreciation_stop_date) and not
                        (i == i_max and li == li_max)):
                    break

                if self.method == 'degr-linear' \
                        and asset_sign * (fy_amount - fy_amount_check) < 0:
                    break

                if i == 0 and li == 0:
                    amount = self._get_first_period_amount(
                        table, entry, depreciation_start_date, line_dates)
                    amount = round(amount, digits)
                else:
                    amount = entry.get('period_amount')

                # last year, last entry
                # Handle rounding deviations.
                if i == i_max and li == li_max:
                    amount = remaining_value
                    remaining_value = 0.0
                else:
                    remaining_value -= amount
                fy_amount_check += amount
                line = {
                    'date': line_date,
                    'amount': amount,
                    'depreciated_value': depreciated_value,
                    'remaining_value': remaining_value,
                }
                lines.append(line)
                depreciated_value += amount

            # Handle rounding and extended/shortened FY deviations.
            #
            # Remark:
            # In account_asset_management version < 8.0.2.8.0
            # the FY deviation for the first FY
            # was compensated in the first FY depreciation line.
            # The code has now been simplified with compensation
            # always in last FT depreciation line.
            method_time = self.method_time

            if self._context.get('bg_asset_line'):
                method_time = self.method_tax_time

            if method_time in ['year', 'month']:
                if round(fy_amount_check - fy_amount, digits) != 0:
                    diff = fy_amount_check - fy_amount
                    amount = amount - diff
                    remaining_value += diff
                    lines[-1].update({
                        'amount': amount,
                        'remaining_value': remaining_value,
                    })
                    depreciated_value -= diff

            if not lines:
                table.pop(i)
            else:
                entry['lines'] = lines
            line_dates = line_dates[li:]

        for i, entry in enumerate(table):
            if not entry['fy_amount']:
                entry['fy_amount'] = sum(
                    [l['amount'] for l in entry['lines']])

    def _compute_depreciation_table(self):

        table = []
        method_time = self.method_time

        if self._context.get('bg_asset_line'):
            method_time = self.method_tax_time

        if method_time in ['year', 'month', 'percentage', 'number'] and not self.method_number:
            return table

        company = self.company_id
        init_flag = False
        asset_date_start = dt.strptime(self.date_start, '%Y-%m-%d')
        if self._context.get('bg_asset_line'):
            asset_date_start = asset_date_start + relativedelta(months=1, day=1)
        fy = company.find_daterange_fy(asset_date_start)
        fiscalyear_lock_date = company.fiscalyear_lock_date
        if fiscalyear_lock_date and fiscalyear_lock_date >= self.date_start:
            init_flag = True
        if fy:
            fy_id = fy.id
            fy_date_start = dt.strptime(fy.date_start, '%Y-%m-%d')
            fy_date_stop = dt.strptime(fy.date_end, '%Y-%m-%d')
        else:
            # The following logic is used when no fiscal year
            # is defined for the asset start date:
            # - We lookup the first fiscal year defined in the system
            # - The 'undefined' fiscal years are assumed to be years
            #   with a duration equal to a calendar year
            first_fy = self.env['date.range'].search(
                [('company_id', '=', self.company_id.id),
                 ('type_id.fiscal_year', '=', True)],
                order='date_end ASC', limit=1)
            if not first_fy:
                raise UserError(
                    _("No Fiscal Year defined."))
            first_fy_date_start = dt.strptime(
                first_fy.date_start, '%Y-%m-%d')
            fy_date_start = first_fy_date_start
            if asset_date_start > fy_date_start:
                asset_ref = self.code and '%s (ref: %s)' \
                    % (self.name, self.code) or self.name
                raise UserError(
                    _("You cannot compute a depreciation table for an asset "
                      "starting in an undefined future fiscal year."
                      "\nPlease correct the start date for asset '%s'.")
                    % asset_ref)
            while asset_date_start < fy_date_start:
                fy_date_start = fy_date_start - relativedelta(years=1)
            fy_date_stop = fy_date_start + relativedelta(years=1, days=-1)
            fy_id = False
            fy = DummyFy(
                date_start=fy_date_start.strftime('%Y-%m-%d'),
                date_end=fy_date_stop.strftime('%Y-%m-%d'),
                id=False,
                state='done',
                dummy=True)
            init_flag = True

        depreciation_start_date = self._get_depreciation_start_date(fy)
        depreciation_stop_date = self._get_depreciation_stop_date(
            depreciation_start_date)
        unblock_move = True
        while fy_date_start <= depreciation_stop_date:
            table.append({
                'fy_id': fy_id,
                'date_start': fy_date_start,
                'date_stop': fy_date_stop,
                'init': init_flag})
            fy_date_start = fy_date_stop + relativedelta(days=1)
            fy = company.find_daterange_fy(fy_date_start)
            if fy:
                if (
                    fiscalyear_lock_date and
                    fiscalyear_lock_date >= fy.date_end
                ):
                    init_flag = True
                else:
                    init_flag = False
                fy_date_stop = dt.strptime(fy.date_end, '%Y-%m-%d')
                unblock_move = False
            else:
                fy_date_stop = fy_date_stop + relativedelta(years=1)
                if unblock_move:
                    fiscalyear_lock_date = fy_date_stop.strftime('%Y-%m-%d')
                if (
                    fiscalyear_lock_date and
                    fiscalyear_lock_date >= fy_date_stop.strftime('%Y-%m-%d')
                ):
                    #init_flag = True
                    init_flag = False
                else:
                    init_flag = False
        # Step 1:
        # Calculate depreciation amount per fiscal year.
        # This is calculation is skipped for method_time != 'year'.
        digits = self.env['decimal.precision'].precision_get('Account')
        fy_residual_amount = self.depreciation_base
        i_max = len(table) - 1
        asset_sign = self.depreciation_base >= 0 and 1 or -1
        line_dates = self._compute_line_dates(
            table, depreciation_start_date, depreciation_stop_date)
        for i, entry in enumerate(table):

            if method_time in ('year', 'month', 'percentage'):
                year_amount = self._compute_year_amount(fy_residual_amount)
                if self.method_period in 'year':
                    period_amount = year_amount
                elif self.method_period == 'quarter':
                    period_amount = year_amount / 4
                elif self.method_period == 'month':
                    period_amount = year_amount / 12
                if i == i_max:
                    if self.method in ['linear-limit', 'degr-limit']:
                        fy_amount = fy_residual_amount - self.salvage_value
                    else:
                        fy_amount = fy_residual_amount
                else:
                    firstyear = i == 0 and True or False
                    fy_factor = self._get_fy_duration_factor(
                        entry, firstyear)
                    fy_amount = year_amount * fy_factor
                if asset_sign * (fy_amount - fy_residual_amount) > 0:
                    fy_amount = fy_residual_amount
                period_amount = round(period_amount, digits)
                fy_amount = round(fy_amount, digits)
            else:
                fy_amount = False
                if method_time == 'number':
                    number = self.method_number
                elif method_time == 'end':
                    number = len(line_dates)
                period_amount = round(self.depreciation_base / number, digits)

            entry.update({
                'period_amount': period_amount,
                'fy_amount': fy_amount,
            })
            if method_time in ['year', 'month']:
                fy_residual_amount -= fy_amount
                if round(fy_residual_amount, digits) == 0:
                    break
        i_max = i
        table = table[:i_max + 1]

        # Step 2:
        # Spread depreciation amount per fiscal year
        # over the depreciation periods.
        self._compute_depreciation_table_lines(
            table, depreciation_start_date, depreciation_stop_date,
            line_dates)

        return table

    def _get_depreciation_entry_name(self, seq):
        """ use this method to customise the name of the accounting entry """
        return (self.code or str(self.id)) + '/' + str(seq)


    @api.model
    def _server_compute_entries(self):
        actions = self.env['account.asset.actions']
        actions_now = False
        if self._context.get("date_end", False):
            date_end = self._context['date_end']
        else:
            date_now = fields.Date.today()
            date_end = fields.Datetime.from_string(date_now) - relativedelta(months=1)
            date_end = datetime.date(date_end.year, date_end.month, calendar.monthrange(date_end.year, date_end.month)[-1])
            date_end = fields.Date.to_string(date_end)
        result, error_log = self._compute_entries(date_end, check_triggers=True)
        _logger.info("Server side start: %s:%s:%s" % (date_end, result, error_log))
        if result:
            actions_now = actions.create({
                                        'date_action': date_now,
                                        'date_end': date_end,
                                        'asset_move_ids': [(6, 0, result)],
                                        })
        if actions_now and error_log:
            actions_now.note = _("Compute Assets errors") + ':\n' + error_log
        return actions_now and (actions_now.asset_move_ids, actions_now.note) or False


    @api.multi
    def _compute_entries(self, date_end, check_triggers=False):
        # TODO : add ir_cron job calling this method to
        # generate periodical accounting entries
        result = []
        error_log = ''
        if check_triggers:
            recompute_obj = self.env['account.asset.recompute.trigger']
            recomputes = recompute_obj.sudo().search([('state', '=', 'open')])
        if check_triggers and recomputes:
            trigger_companies = recomputes.mapped('company_id')
            for asset in self:
                if asset.company_id.id in trigger_companies.ids:
                    asset.compute_depreciation_board()

        depreciations = self.env['account.asset.line'].search([
            ('asset_id', 'in', self.ids),
            ('type', '=', 'depreciate'),
            ('init_entry', '=', False),
            ('line_date', '<=', date_end),
            ('move_check', '=', False)],
            order='line_date')
        _logger.info("Compute enteries %s:%s" % (depreciations, date_end))
        for depreciation in depreciations:
            try:
                with self.env.cr.savepoint():
                    result += depreciation.create_move()
            except Exception:
                e = exc_info()[0]
                tb = ''.join(format_exception(*exc_info()))
                asset_ref = depreciation.asset_id.code and '%s (ref: %s)' \
                    % (asset.name, asset.code) or asset.name
                error_log += _(
                    "\nError while processing asset '%s': %s"
                ) % (asset_ref, str(e))
                error_msg = _(
                    "Error while processing asset '%s': \n\n%s"
                ) % (asset_ref, tb)
                _logger.error("%s, %s", self._name, error_msg)

        if check_triggers and recomputes:
            companies = recomputes.mapped('company_id')
            triggers = recomputes.filtered(
                lambda r: r.company_id.id in companies.ids)
            if triggers:
                recompute_vals = {
                    'date_completed': fields.Datetime.now(),
                    'state': 'done',
                }
                triggers.sudo().write(recompute_vals)

        return (result, error_log)

    def _prepare_early_removal(self, date_remove):
        """
        Generate last depreciation entry on the day before the removal date.
        """
        bg_date_remove = fields.Datetime.from_string(date_remove).replace(day=1)
        bg_date_remove = fields.Datetime.to_string(bg_date_remove)
        residual_value = {}
        for asset in self:
            asset_line_obj = self.env['account.asset.line']

            digits = self.env['decimal.precision'].precision_get('Account')

            def _dlines(asset):
                lines = asset.depreciation_line_ids
                dlines = lines.filtered(
                    lambda l: l.type == 'depreciate' and not
                    l.init_entry and not l.move_check)
                dlines = dlines.sorted(key=lambda l: l.line_date)
                return dlines

            dlines = _dlines(asset)
            if not dlines:
                asset.compute_depreciation_board()
                dlines = _dlines(asset)
            first_to_depreciate_dl = dlines[0]

            first_date = first_to_depreciate_dl.line_date
            if date_remove > first_date:
                raise UserError(
                    _("You can't make an early removal if all the depreciation "
                      "lines for previous periods are not posted."))

            if first_to_depreciate_dl.previous_id:
                last_depr_date = first_to_depreciate_dl.previous_id.line_date
            else:
                create_dl = asset_line_obj.search(
                    [('asset_id', '=', asset.id), ('type', '=', 'create')])
                last_depr_date = create_dl.line_date

            period_number_days = (
                datetime.strptime(first_date, '%Y-%m-%d') -
                datetime.strptime(last_depr_date, '%Y-%m-%d')).days
            date_remove = datetime.strptime(date_remove, '%Y-%m-%d')
            new_line_date = date_remove + relativedelta(days=-1)
            to_depreciate_days = (
                new_line_date -
                datetime.strptime(last_depr_date, '%Y-%m-%d')).days
            to_depreciate_amount = round(
                float(to_depreciate_days) / float(period_number_days) *
                first_to_depreciate_dl.amount, digits)
            residual_value[asset] = asset.value_residual - to_depreciate_amount
            if to_depreciate_amount:
                update_vals = {
                    'amount': to_depreciate_amount,
                    'line_date': new_line_date
                }
                first_to_depreciate_dl.write(update_vals)
                dlines[0].create_move()
                dlines -= dlines[0]
            dlines.unlink()
            bg_dlines = asset.depreciation_bg_line_ids.filtered(lambda r: r.line_date >= bg_date_remove)
            bg_dlines.unlink()
        return residual_value

    @api.multi
    def unlink_move(self):
        for asset in self:
            if self._context.get('bg_asset_line'):
                for line in asset.depreciation_bg_line_ids.filtered(lambda r: r.type in ['depreciate', 'remove']):
                    line.unlink()
            else:
                for line in asset.depreciation_line_ids.filtered(lambda r: r.type in ['depreciate', 'remove'] and not r.move_check):
                    line.unlink()
            asset._compute_depreciation()
