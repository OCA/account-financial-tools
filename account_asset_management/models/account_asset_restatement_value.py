# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import datetime

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountAssetRestatementValue(models.Model):
    _name = 'account.asset.restatement.value'
    _description = 'Asset restatement of value table line'
    _order = 'type, line_date'

    name = fields.Char(string='Depreciation Name', size=64, readonly=True)
    asset_id = fields.Many2one(
        comodel_name='account.asset', string='Asset',
        required=True, ondelete='cascade')
    previous_id = fields.Many2one(
        comodel_name='account.asset.line',
        string='Previous Depreciation Line',
        readonly=True)
    parent_state = fields.Selection(
        related='asset_id.state',
        string='State of Asset',
        readonly=True,
    )
    depreciation_base = fields.Float(string='Restatement Depreciation Base', readonly=True, )
    depreciated_value = fields.Float(string='Restatement Depreciated Amount', digits=dp.get_precision('Account'), readonly=True)
    line_date = fields.Date(string='Date', required=True)
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Restatement Entry', readonly=True)
    move_check = fields.Boolean(
        compute='_compute_move_check',
        string='Posted',
        store=True)
    type = fields.Selection(
        selection=[
            ('create', 'Depreciation Base'),
            ('restatement', 'Restatement of value'),
            ('diminution', 'Diminution of asset'),
            ('remove', 'Asset Removal')],
        readonly=True, default='depreciate')
    init_entry = fields.Boolean(
        string='Initial Balance Entry',
        help="Set this flag for entries of previous fiscal years "
             "for which Odoo has not generated accounting entries.")

    @api.depends('move_id')
    @api.multi
    def _compute_move_check(self):
        for line in self:
            line.move_check = bool(line.move_id)

    def get_restatement_value(self, type, line_date, operator='<=', field=False):
        res = 0.0
        if operator == '<=':
            values = self.filtered(lambda r: r.type in type and r.line_date <= line_date)
        elif operator == '=':
            values = self.filtered(lambda r: r.type in type and r.line_date == line_date)
        elif operator == '>=':
            values = self.filtered(lambda r: r.type in type and r.line_date >= line_date)
        elif operator == '<':
            values = self.filtered(lambda r: r.type in type and r.line_date < line_date)
        elif operator == '>':
            values = self.filtered(lambda r: r.type in type and r.line_date > line_date)
        elif operator == '!=':
            values = self.filtered(lambda r: r.type in type and r.line_date != line_date)
        #_logger.info("VALUES %s:%s" % (values, field))
        if field and values:
            for value in values:
                res += getattr(value, field)
            return res
        else:
            return values or res

    @api.multi
    def open_move(self):
        self.ensure_one()
        return {
            'name': _("Journal Entry"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'domain': [('id', '=', self.move_id.id)],
        }

    @api.multi
    def unlink_move(self):
        for line in self:
            move = line.move_id
            if move.state == 'posted':
                move.button_cancel()
            move.with_context(unlink_from_asset=True).unlink()
            # trigger store function
            line.with_context(unlink_from_asset=True).write(
                {'move_id': False})
            if line.parent_state == 'close':
                line.asset_id.write({'state': 'open'})
            elif line.parent_state == 'removed' and line.type == 'remove':
                line.asset_id.write({
                    'state': 'close',
                    'date_remove': False,
                })
                line.unlink()
        return True
