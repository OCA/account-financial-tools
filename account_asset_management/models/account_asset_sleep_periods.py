# Copyright 2009-2018 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class AccountAssetSleepPeriods(models.Model):
    _name = 'account.asset.sleep.periods'
    _description = 'Asset sleep periods'
    _order = 'line_start_date'

    name = fields.Char(string='Ref', readonly=True)
    asset_id = fields.Many2one(
        comodel_name='account.asset', string='Asset',
        required=True, ondelete='cascade')
    parent_state = fields.Selection(
        related='asset_id.state',
        string='State of Asset',
        readonly=True,
    )
    line_start_date = fields.Date(string='Start Date', required=True)
    line_end_date = fields.Date(string='End Date', required=True)
    note = fields.Text('Description')
    line_days = fields.Integer('Sleep days', compute="_compute_line_days")
    line_mounts = fields.Integer('Sleep mounts', compute="_compute_line_days")
    line_fiscal_breaks = fields.Integer('Fiscal break times', compute="_compute_line_days")

    @api.depends('line_start_date', 'line_end_date')
    @api.multi
    def _compute_line_days(self):
        for line in self:
            if line.line_start_date and line.line_end_date:
                line_end_date = fields.Date.from_string(line.line_end_date)
                line_start_date = fields.Date.from_string(line.line_start_date)
                line.line_days = (line_end_date - line_start_date).days
                extra_mount = 0
                if (line_end_date + relativedelta(days=1)).day == 1:
                    extra_mount = 1
                line.line_mounts = (line_end_date.year - line_start_date.year) * 12 + \
                                   (line_end_date.month - line_start_date.month) + extra_mount
                line.line_fiscal_breaks = int(line.line_mounts/12)

    def get_sleep_days(self):
        line_days = 0
        for line in self:
            line_end_date = fields.Date.from_string(line.line_end_date)
            line_start_date = fields.Date.from_string(line.line_start_date)
            days = (line_end_date - line_start_date).days
            extra_mount = 0
            if (line_end_date + relativedelta(days=1)).day == 1:
                extra_mount = 1
            mounts = (line_end_date.year - line_start_date.year) * 12 + \
                     (line_end_date.month - line_start_date.month) + extra_mount
            if int(mounts/12) == mounts/12 and self._context.get('bg_asset_line'):
                line_days += days
            elif not self._context.get('bg_asset_line'):
                line_days += days
        return line_days

    def get_sleep_mounts(self):
        line_mounts = 0
        for line in self:
            line_end_date = fields.Date.from_string(line.line_end_date)
            line_start_date = fields.Date.from_string(line.line_start_date)
            extra_mount = 0
            if (line_end_date + relativedelta(days=1)).day == 1:
                extra_mount = 1
            mounts = (line_end_date.year - line_start_date.year) * 12 + \
                     (line_end_date.month - line_start_date.month) + extra_mount
            if int(mounts/12) == mounts/12 and self._context.get('bg_asset_line'):
                line_mounts += 12*int(mounts/12)
            elif not self._context.get('bg_asset_line'):
                line_mounts += mounts
        return line_mounts

    def get_sleep_days_mounts(self):
        line_mounts = 0
        line_days = 0
        for line in self:
            line_end_date = fields.Date.from_string(line.line_end_date)
            line_start_date = fields.Date.from_string(line.line_start_date)
            days = (line_end_date - line_start_date).days
            extra_mount = 0
            if (line_end_date + relativedelta(days=1)).day == 1:
                extra_mount = 1
            mounts = (line_end_date.year - line_start_date.year) * 12 + \
                     (line_end_date.month - line_start_date.month) + extra_mount
            if int(mounts/12) == mounts/12 and self._context.get('bg_asset_line'):
                line_days += days
                line_mounts += 12*int(mounts/12)
            elif not self._context.get('bg_asset_line'):
                line_days += days
                line_mounts += mounts
            _logger.info("MOUNTS %s:%s(%s):%s" % (mounts, int(mounts/12), int(mounts/12) == mounts/12, self._context))
        return line_days, line_mounts

    def in_sleep_period(self, line_date):
        line_date = fields.Date.to_string(line_date)
        for record in self:
            if len(record.filtered(lambda r: r.line_start_date <= line_date <= r.line_end_date).ids) > 0:
                return True
        return False
