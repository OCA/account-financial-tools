# -*- coding: utf-8 -*-
# Copyright 2010-2012 OpenERP s.a. (<http://openerp.com>).
# Copyright 2014 Noviat nv/sa (www.noviat.com). All rights reserved.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import time
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp import api, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp.tools.translate import _
from openerp.exceptions import RedirectWarning, ValidationError
import logging
_logger = logging.getLogger(__name__)


class DummyFy(object):
    def __init__(self, *args, **argv):
        for key, arg in argv.items():
            setattr(self, key, arg)


class AccountAssetCategory(models.Model):
    _name = 'account.asset.category'
    _description = 'Asset category'
    _order = 'name'

    def _get_method(self):
        return[
            ('linear', _('Linear')),
            ('degressive', _('Degressive')),
            ('degr-linear', _('Degressive-Linear'))
        ]

    name = fields.Char()
    note = fields.Text()
    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        'Analytic Account',
        domain=[
            ('type', '!=', 'view'),
            ('state', 'not in', ('close', 'cancelled'))],
    )
    account_asset_id = fields.Many2one(
        'account.account',
        'Asset Account',
        required=True,
        domain=[('type', '=', 'other')],
    )
    account_depreciation_id = fields.Many2one(
        'account.account',
        'Depreciation Account',
        required=True,
        domain=[('type', '=', 'other')],
    )
    account_expense_depreciation_id = fields.Many2one(
        'account.account',
        'Depr. Expense Account',
        required=True,
        domain=[('type', '=', 'other')],
    )
    account_plus_value_id = fields.Many2one(
        'account.account',
        'Plus-Value Account',
        domain=[('type', '=', 'other')]
    )
    account_min_value_id = fields.Many2one(
        'account.account',
        'Mix-Value Account',
        domain=[('type', '=', 'other')],
    )
    account_residual_value_id = fields.Many2one(
        'account.account',
        'Residual Value Account',
        domain=[('type', '=', 'other')],
    )
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=lambda self: self.env.user.company_id,
    )
    parent_id = fields.Many2one(
        'account.asset.asset',
        'Parent Asset',
        domain=[('type', '=', 'view')],
    )
    method = fields.Selection(
        _get_method,
        'Computation Method',
        required=True,
        default='linear',
        help="Choose the method to use to compute "
             "the amount of depreciation lines.\n"
             "  * Linear: Calculated on basis of: "
             "Gross Value / Number of Depreciations\n"
             "  * Degressive: Calculated on basis of: "
             "Residual Value * Degressive Factor"
             "  * Degressive-Linear (only for Time Method = Year): "
             "Degressive becomes linear when the annual linear "
             "depreciation exceeds the annual degressive depreciation",
    )
    method_number = fields.Integer(
        'Number of Years',
        default=5,
        help='The number of years needed to depreciate your asset.',
    )
    method_period = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ],
        'Period Length',
        required=True,
        default='year',
        help="Period length for the depreciation accounting entries",
    )
    method_progress_factor = fields.Float('Degressive Factor', default=0.3)
    method_time = fields.Selection(
        [('year', 'Number of years')],
        'Time Method',
        required=True,
        default='year',
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n",
    )
    prorata = fields.Boolean(
        'Prorata Temporis',
        help="Indicates that the first depreciation entry for this asset "
             "has to be done from the depreciation start date instead of "
             "the first day of the fiscal year.",
    )
    open_asset = fields.Boolean(
        'Skip Draft State',
        help="Check this if you want to automatically confirm the assets "
             "of this category when created by invoices.",
    )
    active = fields.Boolean(default=True)

    @api.multi
    @api.constrains('method')
    def _check_method(self):
        for rec in self:
            if rec.method == 'degr-linear' and rec.method_time != 'year':
                raise ValidationError(_(
                    "Degressive-Linear is only supported "
                    "for Time Method = Year."))

    @api.onchange('method_time')
    def onchange_method_time(self):
        if self.method_time != 'year':
            self.prorata = True

    @api.model
    def create(self, vals):
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        categ_id = super(AccountAssetCategory, self).create(vals)
        acc_obj = self.env['account.account']
        acc_id = vals.get('account_asset_id')
        if acc_id:
            account = acc_obj.browse(acc_id)
            if not account.asset_category_id:
                account.write({'asset_category_id': categ_id.id})
        return categ_id

    @api.multi
    def write(self, vals):
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        super(AccountAssetCategory, self).write(vals)
        acc_obj = self.env['account.account']
        for categ in self:
            acc_id = vals.get('account_asset_id')
            if acc_id:
                account = acc_obj.browse(acc_id)
                if not account.asset_category_id:
                    account.write({'asset_category_id': categ.id})
        return True


class AccountAssetRecomputeTrigger(models.Model):
    _name = 'account.asset.recompute.trigger'
    _description = "Asset table recompute triggers"

    reason = fields.Char(required=True)
    company_id = fields.Many2one('res.company', 'Company', required=True)
    date_trigger = fields.Datetime(
        'Trigger Date',
        readonly=True,
        help="Date of the event triggering the need to "
             "recompute the Asset Tables.",
    )
    date_completed = fields.Datetime(
        'Completion Date',
        readonly=True,
    )
    state = fields.Selection([
        ('open', 'Open'),
        ('done', 'Done')],
        readonly=True,
        default='open',
    )


class AccountAssetAsset(models.Model):
    _name = 'account.asset.asset'
    _description = 'Asset'
    _order = 'date_start desc, name'
    _parent_store = True

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _('Invalid action!'),
                    _("You can only delete assets in draft state."))
            if rec.account_move_line_ids:
                raise ValidationError(
                    _('Error!'),
                    _("You cannot delete an asset that contains "
                      "posted depreciation lines."))
            parent = rec.parent_id
            super(AccountAssetAsset, self).unlink()
            if parent:
                parent.write({'salvage_value': parent.salvage_value})
        return True

    def _get_period(self):
        return self.env['account.period'].with_context(
            account_period_prefer_normal=True).find()

    def _get_fy_duration(self, fy_id, option='days'):
        """
        Returns fiscal year duration.
        @param option:
        - days: duration in days
        - months: duration in months,
                  a started month is counted as a full month
        - years: duration in calendar years, considering also leap years
        """
        self.env.cr.execute(
            "SELECT date_start, date_stop, "
            "date_stop-date_start+1 AS total_days "
            "FROM account_fiscalyear WHERE id=%s", [fy_id])
        fy_vals = self.env.cr.dictfetchall()[0]
        days = fy_vals['total_days']
        months = (int(fy_vals['date_stop'][:4]) -
                  int(fy_vals['date_start'][:4])) * 12 + \
                 (int(fy_vals['date_stop'][5:7]) -
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
                fy_vals['date_stop'], '%Y-%m-%d')
            fy_year_stop = int(fy_vals['date_stop'][:4])
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

    def _get_fy_duration_factor(self, entry, asset, firstyear):
        """
        localization: override this method to change the logic used to
        calculate the impact of extended/shortened fiscal years
        """
        duration_factor = 1.0
        fy_id = entry['fy_id']
        if asset.prorata:
            if firstyear:
                depreciation_date_start = datetime.strptime(
                    asset.date_start, '%Y-%m-%d')
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
                duration_factor = self._get_fy_duration(fy_id, option='years')
        elif fy_id:
            fy_months = self._get_fy_duration(fy_id, option='months')
            duration_factor = float(fy_months) / 12
        return duration_factor

    def _get_depreciation_start_date(self, asset, fy):
        """
        In case of 'Linear': the first month is counted as a full month
        if the fiscal year starts in the middle of a month.
        """
        if asset.prorata:
            depreciation_start_date = datetime.strptime(
                asset.date_start, '%Y-%m-%d')
        else:
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            depreciation_start_date = datetime(
                fy_date_start.year, fy_date_start.month, 1)
        return depreciation_start_date

    def _get_depreciation_stop_date(self, asset, depreciation_start_date):
        if asset.method_time == 'year':
            depreciation_stop_date = depreciation_start_date + \
                relativedelta(years=asset.method_number, days=-1)
        elif asset.method_time == 'number':
            if asset.method_period == 'month':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=asset.method_number, days=-1)
            elif asset.method_period == 'quarter':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(months=asset.method_number * 3, days=-1)
            elif asset.method_period == 'year':
                depreciation_stop_date = depreciation_start_date + \
                    relativedelta(years=asset.method_number, days=-1)
        elif asset.method_time == 'end':
            depreciation_stop_date = datetime.strptime(
                asset.method_end, '%Y-%m-%d')
        return depreciation_stop_date

    def _compute_year_amount(self, asset, amount_to_depr, residual_amount):
        """
        Localization: override this method to change the degressive-linear
        calculation logic according to local legislation.
        """
        if asset.method_time == 'year':
            divisor = asset.method_number
        elif asset.method_time == 'number':
            if asset.method_period == 'month':
                divisor = asset.method_number / 12.0
            elif asset.method_period == 'quarter':
                divisor = asset.method_number * 3 / 12.0
            elif asset.method_period == 'year':
                divisor = asset.method_number
        elif asset.method_time == 'end':
            duration = \
                (datetime.strptime(asset.method_end, '%Y-%m-%d') -
                 datetime.strptime(asset.date_start, '%Y-%m-%d')).days + 1
            divisor = duration / 365.0
        year_amount_linear = amount_to_depr / divisor
        if asset.method == 'linear':
            return year_amount_linear
        year_amount_degressive = residual_amount * \
            asset.method_progress_factor
        if asset.method == 'degressive':
            return year_amount_degressive
        if asset.method == 'degr-linear':
            if year_amount_linear > year_amount_degressive:
                return year_amount_linear
            else:
                return year_amount_degressive
        else:
            raise ValidationError(
                _('Programming Error!'),
                _("Illegal value %s in asset.method.") % asset.method)

    def _compute_value_depreciated_table(self):
        asset = self
        extra_context = {'company_id': asset.company_id.id}
        self = self.with_context(extra_context)
        table = []
        if not asset.method_number:
            return table

        fy_obj = self.env['account.fiscalyear'].with_context(extra_context)
        init_flag = False
        try:
            fy_id = fy_obj.find(asset.date_start)
            fy = fy_obj.browse(fy_id)
            if fy.state == 'done':
                init_flag = True
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
        except RedirectWarning:
            # The following logic is used when no fiscalyear
            # is defined for the asset start date:
            # - We lookup the first fiscal year defined in the system
            # - The 'undefined' fiscal years are assumed to be years
            # with a duration equals to calendar year
            self.env.cr.execute(
                "SELECT id, date_start, date_stop "
                "FROM account_fiscalyear ORDER BY date_stop ASC LIMIT 1")
            first_fy = self.env.cr.dictfetchone()
            first_fy_date_start = datetime.strptime(
                first_fy['date_start'], '%Y-%m-%d')
            asset_date_start = datetime.strptime(asset.date_start, '%Y-%m-%d')
            fy_date_start = first_fy_date_start
            if asset_date_start > fy_date_start:
                asset_ref = asset.code and '%s (ref: %s)' \
                    % (asset.name, asset.code) or asset.name
                raise ValidationError(_(
                    "Error!"
                    "You cannot compute a depreciation table for an asset "
                    "starting in an undefined future fiscal year."
                    "\nPlease correct the start date for asset '%s'.")
                    % asset_ref)
            while asset_date_start < fy_date_start:
                fy_date_start = fy_date_start - relativedelta(years=1)
            fy_date_stop = fy_date_start + relativedelta(years=1, days=-1)
            fy_id = False
            fy = DummyFy(
                date_start=fy_date_start.strftime('%Y-%m-%d'),
                date_stop=fy_date_stop.strftime('%Y-%m-%d'),
                id=False,
                state='done',
                dummy=True)
            init_flag = True

        depreciation_start_date = self._get_depreciation_start_date(asset, fy)
        depreciation_stop_date = self._get_depreciation_stop_date(
            asset, depreciation_start_date)

        while fy_date_start <= depreciation_stop_date:
            table.append({
                'fy_id': fy_id,
                'date_start': fy_date_start,
                'date_stop': fy_date_stop,
                'init': init_flag})
            fy_date_start = fy_date_stop + relativedelta(days=1)
            try:
                fy_id = fy_obj.find(fy_date_start)
                init_flag = False
            except RedirectWarning:
                fy_id = False
            if fy_id:
                fy = fy_obj.browse(fy_id)
                if fy.state == 'done':
                    init_flag = True
                fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
            else:
                fy_date_stop = fy_date_stop + relativedelta(years=1)

        digits = self.env['decimal.precision'].precision_get('Account')
        amount_to_depr = residual_amount = asset.asset_value

        # step 1: calculate depreciation amount per fiscal year
        fy_residual_amount = residual_amount
        i_max = len(table) - 1
        asset_sign = asset.asset_value >= 0 and 1 or -1
        for i, entry in enumerate(table):
            year_amount = self._compute_year_amount(
                asset,
                amount_to_depr,
                fy_residual_amount)
            if asset.method_period == 'year':
                period_amount = year_amount
            elif asset.method_period == 'quarter':
                period_amount = year_amount/4
            elif asset.method_period == 'month':
                period_amount = year_amount/12
            if i == i_max:
                fy_amount = fy_residual_amount
            else:
                firstyear = i == 0 and True or False
                fy_factor = self._get_fy_duration_factor(
                    entry,
                    asset,
                    firstyear)
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
            period_duration = (asset.method_period == 'year' and 12) \
                or (asset.method_period == 'quarter' and 3) or 1
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
                raise ValidationError(_(
                    "Programming Error!"
                    "Illegal value %s in asset.method_period.")
                    % asset.method_period)
            for line in lines:
                line['depreciated_value'] = amount_to_depr - residual_amount
                residual_amount -= line['amount']
                line['remaining_value'] = residual_amount
            entry['lines'] = lines

        return table

    def _get_depreciation_entry_name(self, seq):
        """ use this method to customise the name of the accounting entry """
        return (self.code or str(self.id)) + '/' + str(seq)

    @api.multi
    def compute_depreciation_board(self):
        depreciation_lin_obj = self.env[
            'account.asset.depreciation.line']
        digits = self.env['decimal.precision'].precision_get('Account')

        for rec in self:
            if rec.value_residual == 0.0:
                continue
            domain = [
                ('asset_id', '=', rec.id),
                ('type', '=', 'depreciate'),
                '|', ('move_check', '=', True), ('init_entry', '=', True)]
            posted_depreciation_line_ids = depreciation_lin_obj.search(
                domain, order='line_date desc')
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_line = posted_depreciation_line_ids[0]
            else:
                last_depreciation_line = False
            domain = [
                ('asset_id', '=', rec.id),
                ('type', '=', 'depreciate'),
                ('move_id', '=', False),
                ('init_entry', '=', False)]
            old_depreciation_line_ids = depreciation_lin_obj.search(domain)
            old_depreciation_line_ids.unlink()
            context = {}
            context['company_id'] = rec.company_id.id

            table = rec.with_context(
                context)._compute_value_depreciated_table()
            if not table:
                continue

            # group lines prior to depreciation start period
            depreciation_start_date = datetime.strptime(
                rec.date_start, '%Y-%m-%d')
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
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_date = datetime.strptime(
                    last_depreciation_line.line_date, '%Y-%m-%d')
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_depreciation_date:
                    raise ValidationError(
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
                    "FROM account_asset_depreciation_line "
                    "WHERE id IN %s",
                    (tuple(posted_depreciation_line_ids.ids),))
                res = self.env.cr.fetchone()
                depreciated_value = res[0]
                residual_amount = rec.asset_value - depreciated_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    entry = table[table_i_start]
                    self.env.cr.execute(
                        "SELECT COALESCE(SUM(amount), 0.0) "
                        "FROM account_asset_depreciation_line "
                        "WHERE id in %s "
                        "      AND line_date >= %s and line_date <= %s",
                        (tuple(posted_depreciation_line_ids.ids),
                         entry['date_start'],
                         entry['date_stop']))
                    res = self.env.cr.fetchone()
                    fy_amount_check = res[0]
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

            seq = len(posted_depreciation_line_ids)
            depr_line_id = last_depreciation_line and last_depreciation_line.id
            last_date = table[-1]['lines'][-1]['date']
            for entry in table[table_i_start:]:
                for line in entry['lines'][line_i_start:]:
                    seq += 1
                    name = rec.with_context(context). \
                        _get_depreciation_entry_name(seq)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        self.env.cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0) "
                            "FROM account_asset_depreciation_line "
                            "WHERE type = 'depreciate' AND line_date < %s "
                            "AND asset_id = %s ",
                            (last_date, rec.id))
                        res = self.env.cr.fetchone()
                        amount = rec.asset_value - res[0]
                    else:
                        amount = line['amount']
                    vals = {
                        'previous_id': depr_line_id,
                        'amount': amount,
                        'asset_id': rec.id,
                        'name': name,
                        'line_date': line['date'].strftime('%Y-%m-%d'),
                        'init_entry': entry['init'],
                    }
                    depr_line_id = depreciation_lin_obj.with_context(
                        context).create(vals).id
                line_i_start = 0
        return True

    @api.multi
    def validate(self):
        for rec in self:
            if rec.type == 'normal' and rec.company_id.currency_id.is_zero(
                    rec.value_residual):
                rec.write({'state': 'close'})
            else:
                rec.write({'state': 'open'})
        return True

    @api.multi
    def remove(self):
        ctx = self.env.context
        for rec in self:
            if rec.value_residual:
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
    def _asset_value_compute(self):
        self.ensure_one()
        if self.type == 'view':
            asset_value = 0.0
        else:
            asset_value = self.purchase_value - self.salvage_value
        return asset_value

    @api.multi
    def _compute_asset_value(self):
        for rec in self:
            if rec.type == 'normal':
                rec.asset_value = rec._asset_value_compute()
            else:
                def _value_get(record):
                    asset_value = record._asset_value_compute()
                    for child_id in record.child_ids:
                        asset_value += \
                            child_id.type == 'normal' and \
                            child_id._asset_value_compute() \
                            or _value_get(child_id)
                    return asset_value
                rec.asset_value = _value_get(rec)

    @api.multi
    def _compute_value_depreciated(self):
        for asset in self:
            child_ids = self.search([
                ('parent_id', 'child_of', [asset.id]),
                ('type', '=', 'normal')])
            if child_ids:
                self.env.cr.execute(
                    "SELECT COALESCE(SUM(amount),0.0) AS amount "
                    "FROM account_asset_depreciation_line "
                    "WHERE asset_id in %s "
                    "AND type in ('depreciate','remove') "
                    "AND (init_entry=TRUE OR move_check=TRUE)",
                    (tuple(child_ids.ids),))
                value_depreciated = self.env.cr.fetchone()[0]
            else:
                value_depreciated = 0.0
            asset.value_residual = \
                asset.asset_value - value_depreciated
            asset.value_depreciated = \
                value_depreciated

    @api.multi
    def _compute_move_line_check(self):
        for rec in self:
            for line in rec.depreciation_line_ids:
                if line.move_id:
                    rec.move_line_check = True
                    continue

    @api.onchange('purchase_value', 'salvage_value')
    def onchange_purchase_salvage_value(self):
        val = {}
        purchase_value = self.purchase_value or 0.0
        salvage_value = self.salvage_value or 0.0
        if purchase_value or salvage_value:
            self.asset_value = purchase_value - salvage_value
        if self:
            aadl_obj = self.env['account.asset.depreciation.line']
            dl_create_ids = aadl_obj.search([
                ('type', '=', 'create'),
                ('asset_id', 'in', self.ids)])
            dl_create_ids.write({
                'amount': val['asset_value'],
                'line_date': self.date_start})

    @api.multi
    @api.depends(
        'purchase_value',
        'salvage_value',
        'parent_id',
        'depreciation_line_ids')
    def _get_assets(self):
        asset_ids = []
        for rec in self:
            def _parent_get(record):
                asset_ids.append(record.id)
                if record.parent_id:
                    _parent_get(record.parent_id)
            _parent_get(rec)
        return asset_ids

    @api.multi
    @api.depends('amount', 'init_entry', 'move_id')
    def _get_assets_from_dl(self):
        asset_ids = []
        for dl in filter(
                lambda x: x.type in ['depreciate', 'remove'] and (
                    x.init_entry or x.move_id), self):
            res = []

            def _parent_get(record):
                res.append(record.id)
                if record.parent_id:
                    res.append(_parent_get(record.parent_id))

            _parent_get(dl.asset_id)
            for asset_id in res:
                if asset_id not in asset_ids:
                    asset_ids.append(asset_id)
        return asset_ids

    def _get_method(self):
        return self.env['account.asset.category']._get_method()

    account_move_line_ids = fields.One2many(
        'account.move.line',
        'asset_id',
        'Entries',
        readonly=True,
    )
    move_line_check = fields.Boolean(
        'Has accounting entries?',
        compute='_compute_move_line_check',
    )
    name = fields.Char(
        'Asset Name',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    code = fields.Char(
        'Reference',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    purchase_value = fields.Float(
        'Purchase Value',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="\nThe Asset Value is calculated as follows:"
             "\nPurchase Value - Salvage Value.",
    )
    asset_value = fields.Float(
        'Asset Value',
        compute=_compute_asset_value,
        digits=dp.get_precision('Account'),
        help="This amount represent the initial value of the asset.",
    )
    value_residual = fields.Float(
        'Residual Value',
        compute='_compute_value_depreciated',
        digits=dp.get_precision('Account'),
    )
    value_depreciated = fields.Float(
        'Depreciated Value',
        digits=dp.get_precision('Account'),
        compute='_compute_value_depreciated',
    )
    salvage_value = fields.Float(
        'Salvage Value',
        digits=dp.get_precision('Account'),
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="The estimated value that an asset will realize upon "
             "its sale at the end of its useful life.\n"
             "This value is used to determine the depreciation amounts.",
    )
    note = fields.Text()
    category_id = fields.Many2one(
        'account.asset.category',
        'Asset Category',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    parent_id = fields.Many2one(
        'account.asset.asset',
        'Parent Asset',
        readonly=True,
        states={'draft': [('readonly', False)]},
        domain=[('type', '=', 'view')],
        ondelete='restrict',
    )
    parent_left = fields.Integer('Parent Left')
    parent_right = fields.Integer('Parent Right')
    child_ids = fields.One2many(
        'account.asset.asset',
        'parent_id',
        'Child Assets',
    )
    date_start = fields.Date(
        'Asset Start Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="You should manually add depreciation lines "
             "with the depreciations of previous fiscal years "
             "if the Depreciation Start Date is different from the date "
             "for which accounting entries need to be generated.",
    )
    date_remove = fields.Date(
        'Asset Removal Date',
        readonly=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Running'),
        ('close', 'Close'),
        ('removed', 'Removed'),
        ],
        'Status',
        required=True,
        default='draft',
        help="When an asset is created, the status is 'Draft'.\n"
             "If the asset is confirmed, the status goes in 'Running' "
             "and the depreciation lines can be posted "
             "to the accounting.\n"
             "If the last depreciation line is posted, "
             "the asset goes into the 'Close' status.\n"
             "When the removal entries are generated, "
             "the asset goes into the 'Removed' status.",
    )
    active = fields.Boolean('Active', default=True)
    partner_id = fields.Many2one(
        'res.partner',
        'Partner',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    method = fields.Selection(
        _get_method,
        'Computation Method',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Choose the method to use to compute "
             "the amount of depreciation lines.\n"
             "  * Linear: Calculated on basis of: "
             "Gross Value / Number of Depreciations\n"
             "  * Degressive: Calculated on basis of: "
             "Residual Value * Degressive Factor"
             "  * Degressive-Linear (only for Time Method = Year): "
             "Degressive becomes linear when the annual linear "
             "depreciation exceeds the annual degressive depreciation",
    )
    method_number = fields.Integer(
        'Number of Years',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="The number of years needed to depreciate your asset",
    )
    method_period = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ],
        'Period Length',
        required=True,
        readonly=True,
        default='year',
        states={'draft': [('readonly', False)]},
        help="Period length for the depreciation accounting entries",
    )
    method_end = fields.Date(
        'Ending Date',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    method_progress_factor = fields.Float(
        'Degressive Factor',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    method_time = fields.Selection(
        [('year', 'Number of years')],
        'Time Method',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Choose the method to use to compute the dates and "
             "number of depreciation lines.\n"
             "  * Number of Years: Specify the number of years "
             "for the depreciation.\n"
    )
    prorata = fields.Boolean(
        'Prorata Temporis',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help="Indicates that the first depreciation entry for this asset "
             "have to be done from the depreciation start date instead "
             "of the first day of the fiscal year.",
    )
    history_ids = fields.One2many(
        'account.asset.history',
        'asset_id',
        'History',
        readonly=True,
    )
    depreciation_line_ids = fields.One2many(
        'account.asset.depreciation.line',
        'asset_id',
        'Depreciation Lines',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    type = fields.Selection([
        ('view', 'View'),
        ('normal', 'Normal'),
        ],
        'Type',
        required=True,
        readonly=True,
        default='normal',
        states={'draft': [('readonly', False)]},
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        readonly=True,
        default=lambda self: self.env.user.company_id,
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        string='Company Currency',
        readonly=True,
    )
    account_analytic_id = fields.Many2one(
        'account.analytic.account',
        'Analytic account',
        domain=[
            ('type', '!=', 'view'),
            ('state', 'not in', ('close', 'cancelled'))]
    )

    @api.constrains('parent_id')
    def _check_recursion(self, parent=None):
        err = super(AccountAssetAsset, self)._check_recursion(parent=parent)
        if not err:
            raise ValidationError(_(
                "Error ! You can not create recursive assets."))

    @api.constrains('method')
    def _check_method(self):
        for rec in self:
            if rec.method == 'degr-linear' and rec.method_time != 'year':
                raise ValidationError(_(
                    "Degressive-Linear is only supported "
                    "for Time Method = Year."))

    @api.onchange('type')
    def onchange_type(self):
        if self.type == 'view':
            self.date_start = False
            self.category_id = False
            self.purchase_value = 0
            self.salvage_value = 0
            self.code = False
        self.depreciation_line_ids.unlink()

    @api.onchange('category_id')
    def onchange_category_id(self):
        if not all(self.depreciation_line_ids.mapped('move_id')):  # TODO check
            raise ValidationError(_(
                "You cannot change the category of an asset "
                "with accounting entries."))
        self.parent_id = self.category_id.parent_id.id
        self.method = self.category_id.method
        self.method_number = self.category_id.method_number
        self.method_time = self.category_id.method_time
        self.method_period = self.category_id.method_period
        self.method_progress_factor = self.category_id.method_progress_factor
        self.prorata = self.category_id.prorata
        self.account_analytic_id = self.category_id.account_analytic_id.id

    @api.onchange('method_time')
    def onchange_method_time(self):
        if self.method_time != 'year':
            self.prorata = True

    @api.multi
    def copy(self, default=None):
        default.update({
            'depreciation_line_ids': [],
            'account_move_line_ids': [],
            'state': 'draft',
            'history_ids': []})
        return super(AccountAssetAsset, self).copy(default)

    def _compute_entries(self, period_id, check_triggers=False):
        result = []
        depreciation_obj = self.env['account.asset.depreciation.line']
        if check_triggers:
            recompute_obj = self.env['account.asset.recompute.trigger']
            recompute_ids = recompute_obj.sudo().search([
                ('state', '=', 'open')])
            if recompute_ids:
                recompute_triggers = recompute_ids.read(['company_id'])
        for rec in self:
            depreciation_ids = depreciation_obj.search([
                ('asset_id', '=', rec.id),
                ('type', '=', 'depreciate'),
                ('init_entry', '=', False),
                ('line_date', '<', period_id.date_start),
                ('move_check', '=', False)])
            if depreciation_ids:
                asset_ref = ''
                for line in depreciation_ids:
                    asset_ref += rec.code and '%s (ref: %s)' \
                        % (rec.name, rec.code) or rec.name
                raise ValidationError(
                    _("Asset '%s' contains unposted lines "
                      "prior to the selected period."
                      "\nPlease post these entries first !") % asset_ref)
            if check_triggers and recompute_ids:
                triggers = filter(
                    lambda x: x['company_id'][0] == rec.company_id.id,
                    recompute_triggers)
                if triggers:
                    rec.compute_depreciation_board()
        depreciation_ids = depreciation_obj.search([
            ('asset_id', 'in', self.ids),
            ('type', '=', 'depreciate'),
            ('init_entry', '=', False),
            ('line_date', '<=', period_id.date_stop),
            ('line_date', '>=', period_id.date_start),
            ('move_check', '=', False)])
        for depreciation in depreciation_ids:
            self = self.with_context({
                'depreciation_date': depreciation.line_date})
            result += depreciation.create_move()

        if check_triggers and recompute_ids:
            asset_company_ids = set([x.company_id.id for x in self])
            triggers = filter(
                lambda x: x['company_id'][0] in asset_company_ids,
                recompute_triggers)
            if triggers:
                recompute_vals = {
                    'date_completed': fields.Datetime.now(),
                    'state': 'done',
                }
                trigger_ids = [x['id'] for x in triggers]
                recompute_obj.sudo().write(trigger_ids, recompute_vals)
        return result

    @api.model
    def create(self, vals):
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        asset = super(AccountAssetAsset, self).create(vals)
        if self.env.context.get('create_asset_from_move_line'):
            # Trigger compute of asset_value
            asset.write({'salvage_value': 0.0})
        if asset.type == 'normal':
            # create first asset line
            asset_line_obj = self.env['account.asset.depreciation.line']
            line_name = asset._get_depreciation_entry_name(0)
            asset_line_vals = {
                'amount': asset.asset_value,
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
        for rec in self:
            asset_type = vals.get('type') or rec.type
            super(AccountAssetAsset, rec).write(vals)
            if asset_type == 'view' or \
                    self.env.context.get('asset_validate_from_write'):
                continue
            if rec.category_id.open_asset and \
                    self.env.context.get('create_asset_from_move_line'):
                rec.compute_depreciation_board()
                # extra context to avoid recursion
                rec.with_context(asset_validate_from_write=True).validate()
        return True

    def open_entries(self):
        self.env.cr.execute(
            "SELECT move_id, date FROM account_move_line "
            "WHERE asset_id IN %s ORDER BY date ASC",
            (tuple(self.ids),))
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


class AccountAssetDepreciationLine(models.Model):
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    @api.multi
    def _compute_depreciated_value(self):
        self._compute()

    @api.multi
    def _compute_remaining_value(self):
        for index, rec in enumerate(self.filtered(
                lambda rec: rec.type == 'depreciate').sorted('line_date')):
            asset_value = rec.asset_id.asset_value
            if index == 0:
                depreciated_value = rec.previous_id and \
                    (asset_value - rec.previous_id.remaining_value) or 0.0
                remaining_value = asset_value - depreciated_value \
                    - rec.amount
            else:
                depreciated_value += rec.previous_id.amount
                remaining_value -= rec.amount
            rec.depreciated_value = depreciated_value
            rec.remaining_value = remaining_value

    @api.multi
    @api.depends('move_id')
    def _compute_move_check(self):
        for rec in self:
            rec.move_check = bool(rec.move_id)

    _order = 'type, line_date'
    name = fields.Char('Depreciation Name', size=64, readonly=True)
    asset_id = fields.Many2one(
        'account.asset.asset',
        'Asset',
        required=True,
        ondelete='cascade',
    )
    previous_id = fields.Many2one(
        'account.asset.depreciation.line',
        'Previous Depreciation Line',
        readonly=True,
    )
    parent_state = fields.Selection(
        related='asset_id.state',
        string='State of Asset',
    )
    asset_value = fields.Float(
        related='asset_id.asset_value',
        string='Asset Value',
    )
    amount = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Account'),
        required=True,
    )
    remaining_value = fields.Float(
        compute='_compute_remaining_value',
        digits_compute=dp.get_precision('Account'),
        string='Next Period Depreciation',
        store=True,
    )
    depreciated_value = fields.Float(
        compute='_compute_depreciated_value',
        digits=dp.get_precision('Account'),
        string='Amount Already Depreciated',
        store=True,
    )
    line_date = fields.Date('Date', required=True)
    move_id = fields.Many2one(
        'account.move',
        'Depreciation Entry',
        readonly=True,
    )
    move_check = fields.Boolean(
        compute='_compute_move_check',
        string='Posted',
        store=True,
    )
    type = fields.Selection([
        ('create', 'Asset Value'),
        ('depreciate', 'Depreciation'),
        ('remove', 'Asset Removal'),
        ],
        readonly=True,
        default='depreciate',
    )
    init_entry = fields.Boolean(
        'Initial Balance Entry',
        help="Set this flag for entries of previous fiscal years "
             "for which OpenERP has not generated accounting entries.",
    )

    @api.onchange('amount')
    def onchange_amount(self):
        if self.type == 'depreciate':
            self.remaining_value = self.asset_value - \
                self.depreciated_value - self.amount

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.type == 'create':
                raise ValidationError(_(
                    "You cannot remove an asset line "
                    "of type 'Asset Value'."))
            elif rec.move_id:
                raise ValidationError(_(
                    "You cannot delete a depreciation line with "
                    "an associated accounting entry."))
            previous_id = rec.previous_id and rec.previous_id.id or False
            self.env.cr.execute(
                "SELECT id FROM account_asset_depreciation_line "
                "WHERE previous_id = %s", rec.id)
            next = self.env.cr.fetchone()
            if next:
                next_id = next[0]
                self.browse(next_id).write({'previous_id': previous_id})
        return super(AccountAssetDepreciationLine, self).unlink()

    @api.multi
    def write(self, vals):
        for rec in self:
            if vals.keys() == ['move_id'] and not vals['move_id']:
                # allow to remove an accounting entry via the
                # 'Delete Move' button on the depreciation lines.
                if not self.env.context.get('unlink_from_asset'):
                    raise ValidationError(
                        _("You are not allowed to remove an accounting entry "
                          "linked to an asset."
                          "\nYou should remove such entries from the asset."))
            elif vals.keys() == ['asset_id']:
                continue
            elif rec.move_id and not self.env.context.get(
                    'allow_asset_line_update'):
                raise ValidationError(
                    _("You cannot change a depreciation line "
                      "with an associated accounting entry."))
            elif vals.get('init_entry'):
                self.env.cr.execute(
                    "SELECT id "
                    "FROM account_asset_depreciation_line "
                    "WHERE asset_id = %s AND move_check = TRUE "
                    "AND type = 'depreciate' AND line_date <= %s LIMIT 1",
                    (rec.asset_id.id, rec.line_date))
                res = self.env.cr.fetchone()
                if res:
                    raise ValidationError(
                        _("You cannot set the 'Initial Balance Entry' flag "
                          "on a depreciation line "
                          "with prior posted entries."))
            elif vals.get('line_date'):
                self.env.cr.execute(
                    "SELECT id "
                    "FROM account_asset_depreciation_line "
                    "WHERE asset_id = %s "
                    "AND (init_entry=TRUE OR move_check=TRUE)"
                    "AND line_date > %s LIMIT 1",
                    (rec.asset_id.id, vals['line_date']))
                res = self.env.cr.fetchone()
                if res:
                    raise ValidationError(
                        _("You cannot set the date on a depreciation line "
                          "prior to already posted entries."))
        return super(AccountAssetDepreciationLine, self).write(vals)

    def _setup_move_data(self, depreciation_line, depreciation_date,
                         period_id):
        asset = depreciation_line.asset_id
        move_data = {
            'name': asset.name,
            'date': depreciation_date,
            'ref': depreciation_line.name,
            'period_id': period_id.id,
            'journal_id': asset.category_id.journal_id.id,
        }
        return move_data

    def _setup_move_line_data(self, depreciation_line, depreciation_date,
                              period_id, account_id, type, move_id):
        asset = depreciation_line.asset_id
        amount = depreciation_line.amount
        analytic_id = False
        if type == 'depreciation':
            debit = amount < 0 and -amount or 0.0
            credit = amount > 0 and amount or 0.0
        elif type == 'expense':
            debit = amount > 0 and amount or 0.0
            credit = amount < 0 and -amount or 0.0
            analytic_id = asset.account_analytic_id.id
        move_line_data = {
            'name': asset.name,
            'ref': depreciation_line.name,
            'move_id': move_id.id,
            'account_id': account_id,
            'credit': credit,
            'debit': debit,
            'period_id': period_id.id,
            'journal_id': asset.category_id.journal_id.id,
            'partner_id': asset.partner_id.id,
            'analytic_account_id': analytic_id,
            'date': depreciation_date,
            'asset_id': asset.id,
        }
        return move_line_data

    def create_move(self):
        asset_obj = self.env['account.asset.asset']
        period_obj = self.env['account.period']
        move_obj = self.env['account.move']
        move_line_obj = self.env['account.move.line']
        created_move_ids = []
        asset_ids = []
        for line in self:
            asset = line.asset_id
            if asset.method_time == 'year':
                depreciation_date = line.env.context.get(
                    'depreciation_date') or line.line_date
            else:
                depreciation_date = line.env.context.get(
                    'depreciation_date') or time.strftime('%Y-%m-%d')
            period_ids = period_obj.with_context(
                account_period_prefer_normal=True).find(
                    depreciation_date)
            period_id = period_ids and period_ids[0] or False
            move_id = move_obj.create(
                self._setup_move_data(
                    line, depreciation_date, period_id))
            depr_acc_id = asset.category_id.account_depreciation_id.id
            exp_acc_id = asset.category_id.account_expense_depreciation_id.id
            move_line_obj.with_context(allow_asset=True).create(
                self._setup_move_line_data(
                    line,
                    depreciation_date,
                    period_id,
                    depr_acc_id,
                    'depreciation', move_id))
            move_line_obj.with_context(allow_asset=True).create(
                self._setup_move_line_data(
                    line,
                    depreciation_date,
                    period_id,
                    exp_acc_id,
                    'expense',
                    move_id))
            line.with_context(allow_asset_line_update=True).write(
                {'move_id': move_id.id})
            created_move_ids.append(move_id.id)
            asset_ids.append(asset.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(asset_ids):
            if asset.company_id.currency_id.is_zero(asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids

    def open_move(self):
        self.ensure_one()
        for line in self:
            return {
                'name': _("Journal Entry"),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': self.env.context,
                'nodestroy': True,
                'domain': [('id', '=', line.move_id.id)],
            }

    def unlink_move(self):
        for line in self:
            move = line.move_id
            if move.state == 'posted':
                move.button_cancel()
            move.with_context(unlink_from_asset=True).unlink()
            # trigger store function
            line.with_context(unlink_from_asset=True).write({'move_id': False})
            if line.parent_state == 'close':
                line.asset_id.write({'state': 'open'})
            elif line.parent_state == 'removed' and line.type == 'remove':
                line.asset_id.write({'state': 'close'})
                line.unlink()
        return True


class AccountAssetHistory(models.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _order = 'date desc'

    name = fields.Char('History name')
    user_id = fields.Many2one(
        'res.users',
        'User',
        required=True,
        default=lambda self: self.env.uid,
    )
    date = fields.Date('Date', required=True, default=fields.Date.today())
    asset_id = fields.Many2one(
        'account.asset.asset',
        'Asset',
        required=True,
        ondelete='cascade',
    )
    method_time = fields.Selection([
        ('year', 'Number of Years'),
        ],
        'Time Method',
        required=True,
    )
    method_number = fields.Integer(
        'Number of Years',
        help="The number of years needed to depreciate your asset",
    )
    method_period = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ],
        'Period Length',
        help="Period length for the depreciation accounting entries",
    )
    method_end = fields.Date('Ending date')
    note = fields.Text()
