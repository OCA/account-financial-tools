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

from datetime import datetime
from dateutil.relativedelta import relativedelta
import calendar
import logging
from odoo import api, fields, exceptions, models, _
from odoo.addons.decimal_precision import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


_logger = logging.getLogger(__name__)


class dummy_datarange(object):
    def __init__(self, *args, **argv):
        for key, arg in argv.items():
            setattr(self, key, arg)


class AccountAsset(models.Model):
    _name = 'account.asset'
    _description = 'Asset'
    _order = 'date_start desc, name'
    _parent_store = True

    @api.multi
    def unlink(self):
        for asset in self:
            if asset.state != 'draft':
                raise exceptions.UserError(
                    _("You can only delete assets in draft state."))
            if asset.account_move_line_ids:
                raise exceptions.UserError(
                    _("You cannot delete an asset that contains "
                      "posted depreciation lines."))
            return super(AccountAsset, self).unlink()

    @api.model
    def _get_fy_duration(self, datarange_id, option='days'):
        """
        Returns fiscal year duration.
        @param option:
        - days: duration in days
        - months: duration in months,
                  a started month is counted as a full month
        - years: duration in calendar years, considering also leap years
        """
        # TODO replace by orm in v10
        self.env.cr.execute(
            "SELECT date_start, date_end, "
            "date_end-date_start+1 AS total_days "
            "FROM date_range WHERE id=%s" % datarange_id)
        fy_vals = self.env.cr.dictfetchall()[0]
        days = fy_vals['total_days']
        months = (int(fy_vals['date_end'][:4]) -
                  int(fy_vals['date_start'][:4])) * 12 + \
                 (int(fy_vals['date_end'][5:7]) -
                  int(fy_vals['date_start'][5:7])) + 1
        if option == 'days':
            return days
        elif option == 'months':
            return months
        elif option == 'years':
            fy_date_start = datetime.strptime(
                fy_vals['date_start'], '%Y-%m-%d')
            fy_year_start = int(fy_vals['date_start'][:4])
            fy_date_stop = datetime.strptime(
                fy_vals['date_end'], '%Y-%m-%d')
            fy_year_stop = int(fy_vals['date_end'][:4])
            year = fy_year_start
            cnt = fy_year_stop - fy_year_start + 1
            for i in range(cnt):
                cy_days = calendar.isleap(year) and 366 or 365
                if i == 0:  # first year
                    if fy_date_stop.year == year:
                        duration = (fy_date_stop - fy_date_start).days + 1
                    else:
                        duration = (
                            datetime(year, 12, 31) - fy_date_start).days + 1
                    factor = float(duration) / cy_days
                elif i == cnt - 1:  # last year
                    duration = (
                        fy_date_stop - datetime(year, 01, 01)).days + 1
                    factor += float(duration) / cy_days
                else:
                    factor += 1.0
                year += 1
            return factor

    @api.multi
    def _get_fy_duration_factor(self, entry, firstyear):
        """
        localization: override this method to change the logic used to
        calculate the impact of extended/shortened fiscal years
        """
        self.ensure_one()
        duration_factor = 1.0
        daterange_id = entry['fy_range_id']
        if self.prorata:
            if firstyear:
                depreciation_date_start = datetime.strptime(
                    self.date_start, '%Y-%m-%d')
                fy_date_stop = entry['date_stop']
                first_fy_asset_days = \
                    (fy_date_stop - depreciation_date_start).days + 1
                if daterange_id:
                    first_fy_duration = self._get_fy_duration(
                        daterange_id, option='days')
                    first_fy_year_factor = self._get_fy_duration(
                        daterange_id, option='years')
                    duration_factor = \
                        float(first_fy_asset_days) / first_fy_duration \
                        * first_fy_year_factor
                else:
                    first_fy_duration = \
                        calendar.isleap(entry['date_start'].year) \
                        and 366 or 365
                    duration_factor = \
                        float(first_fy_asset_days) / first_fy_duration
            elif daterange_id:
                duration_factor = self._get_fy_duration(
                    cr, uid, daterange_id, option='years')
        elif daterange_id:
            fy_months = self._get_fy_duration(
                daterange_id, option='months')
            duration_factor = float(fy_months) / 12
        return duration_factor

    @api.multi
    def _get_depreciation_start_date(self, fy_date_start):
        """
        In case of 'Linear': the first month is counted as a full month
        if the fiscal year starts in the middle of a month.
        """
        self.ensure_one()
        if self.prorata:
            depreciation_start_date = datetime.strptime(
                self.date_start, '%Y-%m-%d')
        else:
            depreciation_start_date = datetime(
                fy_date_start.year, fy_date_start.month, 1)
        return depreciation_start_date

    @api.multi
    def _get_depreciation_stop_date(self, depreciation_start_date):
        self.ensure_one()
        if self.method_time == 'year':
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=self.method_number, days=-1)
        elif self.method_time == 'number':
            if self.method_period == 'month':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=self.method_number, days=-1)
            elif self.method_period == 'quarter':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=self.method_number * 3, days=-1)
            elif self.method_period == 'year':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(years=self.method_number, days=-1)
        elif self.method_time == 'end':
            depreciation_stop_date = datetime.strptime(
                self.method_end, '%Y-%m-%d')
        return depreciation_stop_date

    @api.multi
    def _compute_year_amount(self, amount_to_depr, residual_amount):
        """
        Localization: override this method to change the degressive-linear
        calculation logic according to local legislation.
        """
        self.ensure_one()
        if self.method_time == 'year':
            divisor = self.method_number
        elif self.method_time == 'number':
            if self.method_period == 'month':
                divisor = self.method_number / 12.0
            elif self.method_period == 'quarter':
                divisor = self.method_number * 3 / 12.0
            elif self.method_period == 'year':
                divisor = self.method_number
        elif self.method_time == 'end':
            duration = \
                (datetime.strptime(self.method_end, '%Y-%m-%d') -
                 datetime.strptime(self.date_start, '%Y-%m-%d')).days + 1
            divisor = duration / 365.0
        year_amount_linear = amount_to_depr / divisor
        if self.method == 'linear':
            return year_amount_linear
        year_amount_degressive = residual_amount * \
            self.method_progress_factor
        if self.method == 'degressive':
            return year_amount_degressive
        if self.method == 'degr-linear':
            if year_amount_linear > year_amount_degressive:
                return year_amount_linear
            else:
                return year_amount_degressive
        else:
            raise exceptions.ValidationError(
                _("Illegal value %s in asset.method.") % self.method)

    @api.multi
    def _compute_depreciation_table(self):
        self.ensure_one()

        table = []
        if not self.method_number:
            return table

        company = self.company_id
        init_flag = False
        asset_date = datetime.strptime(self.date_start, '%Y-%m-%d')
        fy_range = company.find_daterange_fy(asset_date)
        fiscalyear_lock_date = company.fiscalyear_lock_date
#        fy_dates = company.compute_fiscalyear_dates(asset.date_start)
        if fiscalyear_lock_date > self.date_start:
            init_flag = True
        if fy_range:
            fy_range_id = fy_range.id
            fy_date_start = datetime.strptime(fy_range.date_start, '%Y-%m-%d')
            fy_date_stop = datetime.strptime(fy_range.date_end, '%Y-%m-%d')
        else:
            # The following logic is used when no fiscalyear
            # is defined for the asset start date:
            # - We lookup the first fiscal year defined in the system
            # - The 'undefined' fiscal years are assumed to be years
            # with a duration equals to calendar year
            self.env.cr.execute(
                "SELECT id, date_start, date_end "
                "FROM date_range r JOIN date_range_type t"
                "ON r.type_id = t.id"
                "WHERE r.company_id = %s"
                "ORDER BY date_stop ASC LIMIT 1", (company.id,))
            first_fy = self.env.cr.dictfetchone()
            first_fy_date_start = datetime.strptime(
                first_fy['date_start'], '%Y-%m-%d')
            asset_date_start = datetime.strptime(self.date_start, '%Y-%m-%d')
            fy_date_start = first_fy_date_start
            if asset_date_start > fy_date_start:
                asset_ref = self.code and '%s (ref: %s)' \
                    % (self.name, self.code) or self.name
                raise exceptions.UserError(
                    _("You cannot compute a depreciation table for an asset "
                      "starting in an undefined future fiscal year."
                      "\nPlease correct the start date for asset '%s'.")
                    % asset_ref)
            while asset_date_start < fy_date_start:
                fy_date_start = fy_date_start - relativedelta(years=1)
            fy_date_stop = fy_date_start + relativedelta(years=1, days=-1)
            fy_range_id = False
            fy_range = dummy_datarange(
                date_start=fy_date_start.strftime('%Y-%m-%d'),
                date_stop=fy_date_stop.strftime('%Y-%m-%d'),
                id=False,
                state='done',
                dummy=True)
            init_flag = True

        depreciation_start_date = self._get_depreciation_start_date(
            fy_date_start)
        depreciation_stop_date = self._get_depreciation_stop_date(
            depreciation_start_date)

        while fy_date_start <= depreciation_stop_date:
            table.append({
                'fy_range_id': fy_range_id,
                'date_start': fy_date_start,
                'date_stop': fy_date_stop,
                'init': init_flag})
            fy_date_start = fy_date_stop + relativedelta(days=1)
            fy_range = company.find_daterange_fy(fy_date_start)
            if fy_range:
                init_flag = False
            else:
                fy_range_id = False
            if fy_range:
                fy_range_id = fy_range.id
                fy_range = fy_range[0]
                if fiscalyear_lock_date > fy_range.date_end:
                    init_flag = True
                fy_date_stop = datetime.strptime(
                    fy_range.date_stop, '%Y-%m-%d')
            else:
                fy_date_stop = fy_date_stop + relativedelta(years=1)

        digits = self.env['decimal.precision'].precision_get('Account')
        amount_to_depr = residual_amount = self.depreciation_base

        # step 1: calculate depreciation amount per fiscal year
        fy_residual_amount = residual_amount
        i_max = len(table) - 1
        asset_sign = self.depreciation_base >= 0 and 1 or -1
        for i, entry in enumerate(table):
            year_amount = self._compute_year_amount(
                amount_to_depr, fy_residual_amount)
            if self.method_period == 'year':
                period_amount = year_amount
            elif self.method_period == 'quarter':
                period_amount = year_amount/4
            elif self.method_period == 'month':
                period_amount = year_amount/12
            if i == i_max:
                fy_amount = fy_residual_amount
            else:
                firstyear = i == 0 and True or False
                fy_factor = self._get_fy_duration_factor(entry, firstyear)
                fy_amount = year_amount * fy_factor
            if asset_sign * (fy_amount - fy_residual_amount) > 0:
                fy_amount = fy_residual_amount
            period_amount = round(period_amount, digits)
            fy_amount = round(fy_amount, digits)
            entry.update({
                'period_amount': period_amount,
                'fy_amount': fy_amount,
            })
            fy_residual_amount -= fy_amount
            if round(fy_residual_amount, digits) == 0:
                break
        i_max = i
        table = table[:i_max + 1]

        # step 2: spread depreciation amount per fiscal year
        # over the depreciation periods
        fy_residual_amount = residual_amount
        line_date = False
        for i, entry in enumerate(table):
            period_amount = entry['period_amount']
            fy_amount = entry['fy_amount']
            period_duration = (self.method_period == 'year' and 12) \
                or (self.method_period == 'quarter' and 3) or 1
            if period_duration == 12:
                if asset_sign * (fy_amount - fy_residual_amount) > 0:
                    fy_amount = fy_residual_amount
                lines = [{'date': entry['date_stop'], 'amount': fy_amount}]
                fy_residual_amount -= fy_amount
            elif period_duration in [1, 3]:
                lines = []
                fy_amount_check = 0.0
                if not line_date:
                    if period_duration == 3:
                        m = [x for x in [3, 6, 9, 12]
                             if x >= depreciation_start_date.month][0]
                        line_date = depreciation_start_date + \
                            relativedelta(month=m, day=31)
                    else:
                        line_date = depreciation_start_date + \
                            relativedelta(months=0, day=31)
                while line_date <= \
                        min(entry['date_stop'], depreciation_stop_date) and \
                        asset_sign * (fy_residual_amount - period_amount) > 0:
                    lines.append({'date': line_date, 'amount': period_amount})
                    fy_residual_amount -= period_amount
                    fy_amount_check += period_amount
                    line_date = line_date + \
                        relativedelta(months=period_duration, day=31)
                if i == i_max and \
                        (not lines or
                         depreciation_stop_date > lines[-1]['date']):
                    # last year, last entry
                    period_amount = fy_residual_amount
                    lines.append({'date': line_date, 'amount': period_amount})
                    fy_amount_check += period_amount
                if round(fy_amount_check - fy_amount, digits) != 0:
                    # handle rounding and extended/shortened
                    # fiscal year deviations
                    diff = fy_amount_check - fy_amount
                    fy_residual_amount += diff
                    if i == 0:  # first year: deviation in first period
                        lines[0]['amount'] = period_amount - diff
                    else:       # other years: deviation in last period
                        lines[-1]['amount'] = period_amount - diff
            else:
                raise exceptions.UserError(
                    _("Illegal value %s in asset.method_period.")
                    % self.method_period)
            for line in lines:
                line['depreciated_value'] = amount_to_depr - residual_amount
                residual_amount -= line['amount']
                line['remaining_value'] = residual_amount
            entry['lines'] = lines

        return table

    @api.multi
    def _get_depreciation_entry_name(self, seq):
        """ use this method to customise the name of the accounting entry """
        self.ensure_one()
        return (self.code or str(self.id)) + '/' + str(seq)

    @api.multi
    def compute_depreciation_board(self):
        line_obj = self.env['account.asset.line']
        digits = self.env['decimal.precision'].precision_get('Account')

        for asset in self:
            if asset.value_residual == 0.0:
                continue
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                '|', ('move_check', '=', True), ('init_entry', '=', True)]
            posted_lines = line_obj.search(
                domain, order='line_date desc')
            if (len(posted_lines) > 0):
                last_line = posted_lines[0]
            else:
                last_line = line_obj.browse(False)
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                ('move_id', '=', False),
                ('init_entry', '=', False)]
            old_lines = line_obj.search(domain)
            if old_lines:
                old_lines.unlink()

            table = asset._compute_depreciation_table()
            if not table:
                continue

            # group lines prior to depreciation start period
            depreciation_start_date = datetime.strptime(
                asset.date_start, '%Y-%m-%d')
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
                def group_lines(x, y):
                    y.update({'amount': x['amount'] + y['amount']})
                    return y
                lines1 = [reduce(group_lines, lines1)]
                lines1[0]['depreciated_value'] = 0.0
            table[0]['lines'] = lines1 + lines2

            # check table with posted entries and
            # recompute in case of deviation
            if (len(posted_lines) > 0):
                last_depreciation_date = datetime.strptime(
                    last_line.line_date, '%Y-%m-%d')
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_depreciation_date:
                    raise exceptions.UserError(
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
                self.env.cr.execute(
                    "SELECT COALESCE(SUM(amount), 0.0) "
                    "FROM account_asset_line "
                    "WHERE id IN %s",
                    (tuple(posted_lines.ids),))
                res = self.env.cr.fetchone()
                depreciated_value = res[0]
                residual_amount = asset.depreciation_base - depreciated_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    entry = table[table_i_start]
                    if entry['fy_range_id']:
                        self.env.cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0) "
                            "FROM account_asset_line "
                            "WHERE id in %s "
                            "      AND line_date >= %s and line_date <= %s",
                            (tuple(posted_lines.ids),
                             entry['date_start'],
                             entry['date_stop']))
                        res = self.env.cr.fetchone()
                        fy_amount_check = res[0]
                    else:
                        fy_amount_check = 0.0
                    lines = entry['lines']
                    for line in lines[line_i_start:-1]:
                        line['depreciated_value'] = depreciated_value
                        depreciated_value += line['amount']
                        fy_amount_check += line['amount']
                        residual_amount -= line['amount']
                        line['remaining_value'] = residual_amount
                    lines[-1]['depreciated_value'] = depreciated_value
                    lines[-1]['amount'] = entry['fy_amount'] - fy_amount_check

            else:
                table_i_start = 0
                line_i_start = 0

            seq = len(posted_lines)
            depr_line_id = last_line and last_line.id
            last_date = table[-1]['lines'][-1]['date']
            for entry in table[table_i_start:]:
                for line in entry['lines'][line_i_start:]:
                    seq += 1
                    name = asset._get_depreciation_entry_name(seq)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        self.env.cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0) "
                            "FROM account_asset_line "
                            "WHERE type = 'depreciate' AND line_date < %s "
                            "AND asset_id = %s ",
                            (last_date, asset.id))
                        res = self.env.cr.fetchone()
                        amount = asset.depreciation_base - res[0]
                    else:
                        amount = line['amount']
                    vals = {
                        'previous_id': depr_line_id,
                        'amount': amount,
                        'asset_id': asset.id,
                        'name': name,
                        'line_date': line['date'].strftime('%Y-%m-%d'),
                        'init_entry': entry['init'],
                    }
                    depr_line_id = line_obj.create(vals).id
                line_i_start = 0

        return True

    @api.multi
    def validate(self):
        currency_obj = self.env['res.currency']
        for asset in self:
            if asset.type == 'normal' and currency_obj.is_zero(
                    asset.value_residual):
                asset.write({'state': 'close'})
            else:
                asset.write({'state': 'open'})
        return True

    @api.multi
    def remove(self):
        self.ensure_one()
        ctx = self.env.context.copy()
        ctx.update(dict(active_ids=self.ids, active_id=self[0].id))
        ctx.update({'early_removal': True})
        return {
            'name': _("Generate Asset Removal entries"),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.asset.remove',
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': ctx,
            'nodestroy': True,
        }

    @api.multi
    def set_to_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def _depreciation_base_compute(self):
        self.ensure_one()
        if self.type == 'view':
            depreciation_base = 0.0
        else:
            depreciation_base = self.purchase_value - self.salvage_value
        return depreciation_base

    @api.depends('purchase_value', 'salvage_value', 'parent_id')
    @api.multi
    def _depreciation_base(self):
        for asset in self:
            if asset.type == 'normal':
                self.depreciation_base = asset._depreciation_base_compute()
            else:
                def _value_get(record):
                    depreciation_base = asset._depreciation_base_compute()
                    for rec in record.child_ids:
                        depreciation_base += \
                            rec.type == 'normal' and \
                            rec._depreciation_base_compute() \
                            or _value_get(rec)
                    return depreciation_base
                asset.depreciation_base = _value_get(asset)

    @api.multi
    @api.depends('purchase_value', 'salvage_value',
                 'depreciation_line_ids.amount',
                 'depreciation_line_ids.init_entry',
                 'depreciation_line_ids.move_id')
    def _compute_depreciation(self):
        for asset in self:
            if asset.type != 'view' and self.ids:
                self.env.cr.execute(
                    "SELECT COALESCE(SUM(amount),0.0) AS amount "
                    "FROM account_asset_line "
                    "WHERE asset_id in %s "
                    "AND type in ('depreciate','remove') "
                    "AND (init_entry=TRUE OR move_check=TRUE)",
                    (tuple(asset.ids),))
                value_depreciated = self.env.cr.fetchone()[0]
            else:
                value_depreciated = 0.0
            asset.value_residual = asset.depreciation_base - value_depreciated
            asset.value_depreciated = value_depreciated

    @api.multi
    def _move_line_check(self):
        for asset in self:
            for line in asset.depreciation_line_ids:
                if line.move_id:
                    asset.move_line_check = True
                    continue

    @api.onchange('purchase_value', 'salvage_value')
    def onchange_purchase_salvage_value(self):
        purchase_value = self.purchase_value or 0.0
        salvage_value = self.salvage_value or 0.0
        if purchase_value or salvage_value:
            self.depreciation_base = purchase_value - salvage_value
        if self.ids:
            aadl_obj = self.env['account.asset.line']
            dl_create_lines = aadl_obj.search(
                [('type', '=', 'create'), ('asset_id', 'in', self.ids)])
            dl_create_lines.write({
                'amount': purchase_value - salvage_value,
                'line_date': date_start})

    @api.model
    def _get_company(self):
        return self.env['res.company']._company_default_get('account.asset')

    account_move_line_ids = fields.One2many(
        'account.move.line', 'asset_id', 'Entries', readonly=True, copy=False)
    move_line_check = fields.Boolean(
        compute='_move_line_check', type='boolean',
        string='Has accounting entries')
    name = fields.Char(
        'Asset Name', size=64, required=True,
        readonly=True, states={'draft': [('readonly', False)]})
    code = fields.Char(
        'Reference', size=32, readonly=True,
        states={'draft': [('readonly', False)]})
    purchase_value = fields.Float(
        'Purchase Value', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        help="This amount represent the initial value of the asset.")
    depreciation_base = fields.Float(
        compute='_depreciation_base',
        digits_compute=dp.get_precision('Account'),
        string='Depreciation Base',
        store=True,
        help="\nThe Asset Value is calculated as follows:"
             "\nPurchase Value - Salvage Value.")
    salvage_value = fields.Float(
        string='Salvage Value', digits_compute=dp.get_precision('Account'),
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="The estimated value that an asset will realize upon "
             "its sale at the end of its useful life.\n"
             "This value is used to determine the depreciation amounts.")
    note = fields.Text('Note')
    profile_id = fields.Many2one(
        'account.asset.profile', 'Asset Category',
        change_default=True, readonly=True,
        states={'draft': [('readonly', False)]})
    parent_id = fields.Many2one(
        'account.asset', 'Parent Asset', readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('type', '=', 'view')],
        ondelete='restrict')
    parent_left = fields.Integer('Parent Left', index=True)
    parent_right = fields.Integer('Parent Right', index=True)
    child_ids = fields.One2many(
        'account.asset', 'parent_id', 'Child Assets')
    date_start = fields.Date(
        'Asset Start Date', readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Datetime.now,
        help="You should manually add depreciation lines "
             "with the depreciations of previous fiscal years "
             "if the Depreciation Start Date is different from the date "
             "for which accounting entries need to be generated.")
    date_remove = fields.Date('Asset Removal Date', readonly=True)
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Running'),
            ('close', 'Close'),
            ('removed', 'Removed'),
        ], string='Status', required=True, default='draft', copy='draft',
        help="When an asset is created, the status is 'Draft'.\n"
             "If the asset is confirmed, the status goes in 'Running' "
             "and the depreciation lines can be posted "
             "to the accounting.\n"
             "If the last depreciation line is posted, "
             "the asset goes into the 'Close' status.\n"
             "When the removal entries are generated, "
             "the asset goes into the 'Removed' status.")
    active = fields.Boolean('Active', default=True)
    partner_id = fields.Many2one(
        'res.partner', 'Partner', readonly=True,
        states={'draft': [('readonly', False)]})
    method = fields.Selection(
        selection=lambda self: self.env['account.asset.profile'].
        _get_method(),
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
        'Number of Years', readonly=True,
        states={'draft': [('readonly', False)]}, default=5,
        help="The number of years needed to depreciate your asset")
    method_period = fields.Selection(
        selection=lambda self: self.env['account.asset.profile'].
        _get_method_period(), string='Period Length',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='year',
        help="Period length for the depreciation accounting entries")
    method_end = fields.Date(
        'Ending Date', readonly=True,
        states={'draft': [('readonly', False)]})
    method_progress_factor = fields.Float(
        'Degressive Factor', readonly=True,
        states={'draft': [('readonly', False)]}, default=0.3)
    method_time = fields.Selection(
        selection=lambda self: self.env['account.asset.profile'].
        _get_method_time(), string='Time Method',
        required=True, readonly=True,
        states={'draft': [('readonly', False)]}, default='year',
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
             "  * Number of Depreciations: Fix the number of "
             "depreciation lines and the time between 2 depreciations.\n"
             "  * Ending Date: Choose the time between 2 depreciations "
             "and the date the depreciations won't go beyond."
        )
    prorata = fields.Boolean(
        'Prorata Temporis', readonly=True,
        states={'draft': [('readonly', False)]},
        help="Indicates that the first depreciation entry for this asset "
             "have to be done from the depreciation start date instead "
             "of the first day of the fiscal year.")
    depreciation_line_ids = fields.One2many(
        'account.asset.line', 'asset_id',
        'Depreciation Lines', copy=False,
        readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([
        ('view', 'View'),
        ('normal', 'Normal'),
        ], 'Type',
        required=True, readonly=True, default='normal',
        states={'draft': [('readonly', False)]})
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, readonly=True,
        default=_get_company)
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        store=True, readonly=True)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', 'Analytic account',
        domain=[('type', '!=', 'view'),
                ('state', 'not in', ('close', 'cancelled'))])
    value_residual = fields.Float(
        compute='_compute_depreciation',
        digits_compute=dp.get_precision('Account'),
        string='Residual Value',
        store=True)
    value_depreciated = fields.Float(
        compute='_compute_depreciation',
        digits_compute=dp.get_precision('Account'),
        string='Depreciated Value',
        store=True)

    @api.multi
    @api.constrains('parent_id')
    def _check_recursion(self, parent=None):
        res = super(AccountAsset, self)._check_recursion(parent=parent)
        if not res:
            exceptions.UserError(
                _("Error ! You can not create recursive assets."))
        return res

    @api.multi
    @api.constrains('method')
    def _check_method(self):
        for asset in self:
            if asset.method == 'degr-linear' and asset.method_time != 'year':
                exceptions.UserError(
                    _("Degressive-Linear is only supported for Time Method = "
                      "Year."))

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'view':
            self.date_start = False
            self.profile_id = False
            self.purchase_value = False
            self.salvage_value = False
            self.code = False
        if self.depreciation_line_ids:
            self.depreciation_line_ids.unlink()

    @api.onchange('profile_id')
    def onchange_profile_id(self):
        for line in self.depreciation_line_ids:
            if line.move_id:
                raise exceptions.UserError(
                    _("You cannot change the category of an asset "
                      "with accounting entries."))
        asset_categ_obj = self.pool.get('account.asset.profile')
        if self.profile_id:
            categ = self.profile_id
            self.parent_id = categ.parent_id.id
            self.method = categ.method
            self.method_number = categ.method_number
            self.method_time = categ.method_time
            self.method_period = categ.method_period
            self.method_progress_factor = categ.method_progress_factor
            self.prorata = categ.prorata
            self.account_analytic_id = categ.account_analytic_id.id

    @api.onchange('method_time')
    def onchange_method_time(self):
        if self.method_time != 'year':
            self.prorata = True

    @api.multi
    def _compute_entries(self, date_end, check_triggers=False):
        # To DO : add ir_cron job calling this method to
        # generate periodical accounting entries
        result = []
        depreciation_obj = self.env['account.asset.line']
        if check_triggers:
            recompute_obj = self.env['account.asset.recompute.trigger']
            recomputes = recompute_obj.sudo().search(
                [('state', '=', 'open')])
        if check_triggers and recomputes:
            trigger_companies = triggers.mapped('company_id')
            for asset in self:
                if asset.company_id.id in trigger_companies.ids:
                    asset.compute_depreciation_board()
        depreciations = depreciation_obj.search([
            ('asset_id', 'in', self.ids),
            ('type', '=', 'depreciate'),
            ('init_entry', '=', False),
            ('line_date', '<=', date_end),
            ('move_check', '=', False)], order='line_date')
        for depreciation in depreciations:
            result += depreciation.with_context(
                depreciation_date=depreciation.line_date).create_move()

        if check_triggers and recomputes:
            companies = assets.mapped('company_id')
            triggers = recomputes.filtered(
                lambda r: r.company_id.id in companies.ids)
            if triggers:
                recompute_vals = {
                    'date_completed': time.strftime(
                        DEFAULT_SERVER_DATETIME_FORMAT),
                    'state': 'done',
                }
                triggers.sudo().write(recompute_vals)
        return result

    @api.model
    def create(self, vals):
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        asset = super(AccountAsset, self).create(vals)
        if self.env.context.get('create_asset_from_move_line'):
            # Trigger compute of depreciation_base
            asset.write({'salvage_value': 0.0})
        if asset.type == 'normal':
            # create first asset line
            asset_line_obj = self.env['account.asset.line']
            line_name = asset._get_depreciation_entry_name(0)
            asset_line_vals = {
                'amount': asset.depreciation_base,
                'asset_id': asset.id,
                'name': line_name,
                'line_date': asset.date_start,
                'init_entry': True,
                'type': 'create',
            }
            asset_line = asset_line_obj.create(asset_line_vals)
            if self.env.context.get('create_asset_from_move_line'):
                asset_line.write({'move_id': self.env.context['move_id']})
        return asset

    @api.multi
    def write(self, vals):
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        for asset in self:
            asset_type = vals.get('type') or asset.type
            res = super(AccountAsset, self).write(vals)
            if asset_type == 'view' or \
                    self.env.context.get('asset_validate_from_write'):
                continue
            if asset.profile_id.open_asset and \
                    self.env.context.get('create_asset_from_move_line'):
                asset.compute_depreciation_board()
                # extra context to avoid recursion
                asset.with_context(asset_validate_from_write=True).validate()
        return res

    @api.multi
    def open_entries(self):
        self.env.cr.execute(
            "SELECT move_id, date FROM account_move_line "
            "WHERE asset_id IN %s ORDER BY date ASC", (tuple(self.ids),))
        res = self.env.cr.fetchall()
        am_ids = [x[0] for x in res]
        return {
            'name': _("Journal Entries"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'nodestroy': True,
            'domain': [('id', 'in', am_ids)],
        }

    @api.multi
    def open_move_lines(self):
        self.env.cr.execute(
            "SELECT aml2.id FROM account_move_line aml "
            "INNER JOIN account_move am ON am.id=aml.move_id "
            "INNER JOIN account_move_line aml2 ON aml2.move_id = am.id "
            "WHERE aml.asset_id IN %s",
            (tuple(self.ids),))
        res = self.env.cr.fetchall()
        aml_ids = [x[0] for x in res]
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': self.env.context,
            'nodestroy': True,
            'domain': [('id', 'in', aml_ids)],
        }
