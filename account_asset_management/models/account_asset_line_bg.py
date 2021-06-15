# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountBgAssetLine(models.Model):
    _name = 'account.bg.asset.line'
    _description = 'BG Asset depreciation table line'
    _order = 'line_date'

    name = fields.Char(string='Depreciation Name', size=64, readonly=True)
    asset_id = fields.Many2one(
        comodel_name='account.asset', string='Asset',
        required=True, ondelete='cascade')
    previous_id = fields.Many2one(
        comodel_name='account.bg.asset.line',
        string='Previous Depreciation Line',
        readonly=True)
    parent_state = fields.Selection(
        related='asset_id.state',
        string='State of Asset',
        readonly=True,
    )
    depreciation_base = fields.Float(
        related='asset_id.depreciation_base',
        string='Depreciation Base',
        readonly=True,
    )
    amount = fields.Float(
        string='Amount', digits=dp.get_precision('Account'),
        required=True)
    remaining_value = fields.Float(
        compute='_compute_values',
        digits=dp.get_precision('Account'),
        string='Next Period Depreciation',
        store=True)
    depreciated_value = fields.Float(
        compute='_compute_values',
        digits=dp.get_precision('Account'),
        string='Amount Already Depreciated',
        store=True)
    line_date = fields.Date(string='Date', required=True)
    type = fields.Selection(
        selection=[
            ('create', 'Depreciation Base'),
            ('depreciate', 'Depreciation'),
            ('storno', 'Storno fiscal amount'),
            ('remove', 'Asset Removal')],
        readonly=True, default='depreciate')
    init_entry = fields.Boolean(
        string='Initial Balance Entry',
        help="Set this flag for entries of previous fiscal years "
             "for which Odoo has not generated accounting entries.")
    sleep_period = fields.Boolean(
        string='Sleep period',
        help='This is period not have depreciation if this line available in sleeping periods',
    )

    @api.depends('amount', 'previous_id', 'type')
    @api.multi
    def _compute_values(self):
        dlines = self
        if self.env.context.get('no_compute_asset_line_ids'):
            # skip compute for lines in unlink
            exclude_ids = self.env.context['no_compute_asset_line_ids']
            dlines = self.filtered(lambda l: l.id not in exclude_ids)
        dlines = dlines.filtered(lambda l: l.type == 'depreciate')
        dlines = dlines.sorted(key=lambda l: l.line_date)

        for i, dl in enumerate(dlines):
            coef = 1
            if type == 'storno':
                coef = -1
            if i == 0:
                depreciation_base = dl.depreciation_base
                depreciated_value = dl.previous_id \
                    and (depreciation_base - dl.previous_id.remaining_value) \
                    or 0.0
                remaining_value = \
                    depreciation_base - depreciated_value - dl.amount*coef
            else:
                depreciated_value += dl.previous_id.amount*coef
                remaining_value -= dl.amount*coef
            dl.depreciated_value = depreciated_value
            dl.remaining_value = remaining_value

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.type == 'depreciate':
            self.remaining_value = self.depreciation_base - \
                self.depreciated_value - self.amount

    @api.multi
    def write(self, vals):
        for dl in self:
            if vals.get('line_date'):
                if isinstance(vals['line_date'], datetime.date):
                    vals['line_date'] = fields.Date.to_string(
                        vals['line_date'])
            line_date = vals.get('line_date') or dl.line_date
            asset_lines = dl.asset_id.depreciation_line_ids
            if vals.get('line_date'):
                if dl.type == 'create':
                    check = asset_lines.filtered(
                        lambda l: l.type != 'create' and
                        (l.init_entry or l.move_check) and
                        l.line_date < vals['line_date'])
                    if check:
                        raise UserError(
                            _("You cannot set the Asset Start Date "
                              "after already posted entries."))
                else:
                    check = asset_lines.filtered(
                        lambda l: (l.init_entry or l.move_check) and
                        l.line_date > vals['line_date'] and l != dl)
                    if check:
                        raise UserError(_(
                            "You cannot set the date on a depreciation line "
                            "prior to already posted entries."))
        #_logger.info("Write vals= %s" % (vals))
        return super().write(vals)

    @api.multi
    def unlink(self):
        for dl in self:
            if dl.type == 'create' and dl.amount:
                raise UserError(_(
                    "You cannot remove an asset line "
                    "of type 'Depreciation Base'."))
            previous = dl.previous_id
            next_line = dl.asset_id.depreciation_line_ids.filtered(
                lambda l: l.previous_id == dl and l not in self)
            if next_line:
                next_line.previous_id = previous
        return super(AccountBgAssetLine, self.with_context(
            no_compute_asset_line_ids=self.ids)).unlink()
