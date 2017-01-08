# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) 2010-2012 OpenERP s.a. (<http://openerp.com>).
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

import time
import calendar
from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.osv import fields, orm
from openerp.addons.decimal_precision import decimal_precision as dp
from openerp import tools
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import logging
_logger = logging.getLogger(__name__)


class dummy_fy(object):
    def __init__(self, *args, **argv):
        for key, arg in argv.items():
            setattr(self, key, arg)


class account_asset_category(orm.Model):
    _name = 'account.asset.category'
    _description = 'Asset category'
    _order = 'name'

    def _get_method(self, cr, uid, context=None):
        return[
            ('linear', _('Linear')),
            ('degressive', _('Degressive')),
            ('degr-linear', _('Degressive-Linear'))
        ]

    def _get_method_time(self, cr, uid, context=None):
        return [
            ('year', _('Number of Years')),
            # ('number', _('Number of Depreciations')),
            # ('end', _('Ending Date'))
        ]

    def _get_company(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(
            cr, uid, 'account.asset.category', context=context)

    _columns = {
        'name': fields.char('Name', size=64, required=True, select=1),
        'note': fields.text('Note'),
        'account_analytic_id': fields.many2one(
            'account.analytic.account', 'Analytic account',
            domain=[('type', '!=', 'view'),
                    ('state', 'not in', ('close', 'cancelled'))]),
        'account_asset_id': fields.many2one(
            'account.account', 'Asset Account', required=True,
            domain=[('type', '=', 'other')]),
        'account_depreciation_id': fields.many2one(
            'account.account', 'Depreciation Account', required=True,
            domain=[('type', '=', 'other')]),
        'account_expense_depreciation_id': fields.many2one(
            'account.account', 'Depr. Expense Account', required=True,
            domain=[('type', '=', 'other')]),
        'account_plus_value_id': fields.many2one(
            'account.account', 'Plus-Value Account',
            domain=[('type', '=', 'other')]),
        'account_min_value_id': fields.many2one(
            'account.account', 'Min-Value Account',
            domain=[('type', '=', 'other')]),
        'account_residual_value_id': fields.many2one(
            'account.account', 'Residual Value Account',
            domain=[('type', '=', 'other')]),
        'journal_id': fields.many2one(
            'account.journal', 'Journal', required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True),
        'parent_id': fields.many2one(
            'account.asset.asset',
            'Parent Asset',
            domain=[('type', '=', 'view')]),
        'method': fields.selection(
            _get_method, 'Computation Method',
            required=True,
            help="Choose the method to use to compute "
                 "the amount of depreciation lines.\n"
                 "  * Linear: Calculated on basis of: "
                 "Gross Value / Number of Depreciations\n"
                 "  * Degressive: Calculated on basis of: "
                 "Residual Value * Degressive Factor"
                 "  * Degressive-Linear (only for Time Method = Year): "
                 "Degressive becomes linear when the annual linear "
                 "depreciation exceeds the annual degressive depreciation"),
        'method_number': fields.integer(
            'Number of Years',
            help="The number of years needed to depreciate your asset"),
        'method_period': fields.selection([
            ('month', 'Month'),
            ('quarter', 'Quarter'),
            ('year', 'Year'),
            ], 'Period Length', required=True,
            help="Period length for the depreciation accounting entries"),
        'method_progress_factor': fields.float('Degressive Factor'),
        'method_time': fields.selection(
            _get_method_time,
            'Time Method', required=True,
            help="Choose the method to use to compute the dates and "
                 "number of depreciation lines.\n"
                 "  * Number of Years: Specify the number of years "
                 "for the depreciation.\n"
                 # "  * Number of Depreciations: Fix the number of "
                 # "depreciation lines and the time between 2 depreciations.\n"
                 # "  * Ending Date: Choose the time between 2 depreciations "
                 # "and the date the depreciations won't go beyond."
        ),
        'prorata': fields.boolean(
            'Prorata Temporis',
            help="Indicates that the first depreciation entry for this asset "
                 "has to be done from the depreciation start date instead of "
                 "the first day of the fiscal year."),
        'open_asset': fields.boolean(
            'Skip Draft State',
            help="Check this if you want to automatically confirm the assets "
            "of this category when created by invoices."),
        'active': fields.boolean('Active'),
    }

    _defaults = {
        'active': 1,
        'company_id': _get_company,
        'method': 'linear',
        'method_number': 5,
        'method_time': 'year',
        'method_period': 'year',
        'method_progress_factor': 0.3,
    }

    def _check_method(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.method == 'degr-linear' and asset.method_time != 'year':
                return False
        return True

    _constraints = [(
        _check_method,
        "Degressive-Linear is only supported for Time Method = Year.",
        ['method']
    )]

    def onchange_method_time(self, cr, uid, ids,
                             method_time='number', context=None):
        res = {'value': {}}
        if method_time != 'year':
            res['value'] = {'prorata': True}
        return res

    def create(self, cr, uid, vals, context=None):
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        categ_id = super(account_asset_category, self).create(
            cr, uid, vals, context=context)
        acc_obj = self.pool.get('account.account')
        acc_id = vals.get('account_asset_id')
        if acc_id:
            account = acc_obj.browse(cr, uid, acc_id)
            if not account.asset_category_id:
                acc_obj.write(
                    cr, uid, [acc_id], {'asset_category_id': categ_id})
        return categ_id

    def write(self, cr, uid, ids, vals, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        super(account_asset_category, self).write(cr, uid, ids, vals, context)
        acc_obj = self.pool.get('account.account')
        for categ in self.browse(cr, uid, ids, context):
            acc_id = vals.get('account_asset_id')
            if acc_id:
                account = acc_obj.browse(cr, uid, acc_id)
                if not account.asset_category_id:
                    acc_obj.write(
                        cr, uid, [acc_id], {'asset_category_id': categ.id})
        return True


class account_asset_recompute_trigger(orm.Model):
    _name = 'account.asset.recompute.trigger'
    _description = "Asset table recompute triggers"
    _columns = {
        'reason': fields.char(
            'Reason', size=64, required=True),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True),
        'date_trigger': fields.datetime(
            'Trigger Date',
            readonly=True,
            help="Date of the event triggering the need to "
                 "recompute the Asset Tables."),
        'date_completed': fields.datetime(
            'Completion Date', readonly=True),
        'state': fields.selection(
            [('open', 'Open'), ('done', 'Done')],
            'State',
            readonly=True),
    }
    _defaults = {
        'state': 'open',
    }


class account_asset_asset(orm.Model):
    _name = 'account.asset.asset'
    _description = 'Asset'
    _order = 'date_start desc, name'
    _parent_store = True

    def unlink(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.state != 'draft':
                raise orm.except_orm(
                    _('Invalid action!'),
                    _("You can only delete assets in draft state."))
            if asset.account_move_line_ids:
                raise orm.except_orm(
                    _('Error!'),
                    _("You cannot delete an asset that contains "
                      "posted depreciation lines."))
            parent = asset.parent_id
            super(account_asset_asset, self).unlink(
                cr, uid, [asset.id], context=context)
            if parent:
                # Trigger store function
                parent.write({'salvage_value': parent.salvage_value})
        return True

    def _get_period(self, cr, uid, context=None):
        ctx = dict(context or {}, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        if periods:
            return periods[0]
        else:
            return False

    def _get_fy_duration(self, cr, uid, fy_id, option='days', context=None):
        """
        Returns fiscal year duration.
        @param option:
        - days: duration in days
        - months: duration in months,
                  a started month is counted as a full month
        - years: duration in calendar years, considering also leap years
        """
        cr.execute(
            "SELECT date_start, date_stop, "
            "date_stop-date_start+1 AS total_days "
            "FROM account_fiscalyear WHERE id=%s" % fy_id)
        fy_vals = cr.dictfetchall()[0]
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

    def _get_fy_duration_factor(self, cr, uid, entry,
                                asset, firstyear, context=None):
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
                        cr, uid, fy_id, option='days')
                    first_fy_year_factor = self._get_fy_duration(
                        cr, uid, fy_id, option='years')
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
                    cr, uid, fy_id, option='years')
        elif fy_id:
            fy_months = self._get_fy_duration(
                cr, uid, fy_id, option='months')
            duration_factor = float(fy_months) / 12
        return duration_factor

    def _get_depreciation_start_date(self, cr, uid, asset, fy, context=None):
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

    def _get_depreciation_stop_date(self, cr, uid, asset,
                                    depreciation_start_date, context=None):
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

    def _compute_year_amount(self, cr, uid, asset, amount_to_depr,
                             residual_amount, context=None):
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
            raise orm.except_orm(
                _('Programming Error!'),
                _("Illegal value %s in asset.method.") % asset.method)

    def _compute_depreciation_table(self, cr, uid, asset, context=None):
        if not context:
            context = {}
        context = context.copy()

        table = []
        if not asset.method_number:
            return table

        context['company_id'] = asset.company_id.id
        fy_obj = self.pool.get('account.fiscalyear')
        init_flag = False
        try:
            fy_id = fy_obj.find(cr, uid, asset.date_start, context=context)
            fy = fy_obj.browse(cr, uid, fy_id)
            if fy.state == 'done':
                init_flag = True
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
        except:
            # The following logic is used when no fiscalyear
            # is defined for the asset start date:
            # - We lookup the first fiscal year defined in the system
            # - The 'undefined' fiscal years are assumed to be years
            # with a duration equals to calendar year
            cr.execute(
                "SELECT id, date_start, date_stop "
                "FROM account_fiscalyear ORDER BY date_stop ASC LIMIT 1")
            first_fy = cr.dictfetchone()
            first_fy_date_start = datetime.strptime(
                first_fy['date_start'], '%Y-%m-%d')
            asset_date_start = datetime.strptime(asset.date_start, '%Y-%m-%d')
            fy_date_start = first_fy_date_start
            if asset_date_start > fy_date_start:
                asset_ref = asset.code and '%s (ref: %s)' \
                    % (asset.name, asset.code) or asset.name
                raise orm.except_orm(
                    _('Error!'),
                    _("You cannot compute a depreciation table for an asset "
                      "starting in an undefined future fiscal year."
                      "\nPlease correct the start date for asset '%s'.")
                    % asset_ref)
            while asset_date_start < fy_date_start:
                fy_date_start = fy_date_start - relativedelta(years=1)
            fy_date_stop = fy_date_start + relativedelta(years=1, days=-1)
            fy_id = False
            fy = dummy_fy(
                date_start=fy_date_start.strftime('%Y-%m-%d'),
                date_stop=fy_date_stop.strftime('%Y-%m-%d'),
                id=False,
                state='done',
                dummy=True)
            init_flag = True

        depreciation_start_date = self._get_depreciation_start_date(
            cr, uid, asset, fy, context=context)
        depreciation_stop_date = self._get_depreciation_stop_date(
            cr, uid, asset, depreciation_start_date, context=context)

        while fy_date_start <= depreciation_stop_date:
            table.append({
                'fy_id': fy_id,
                'date_start': fy_date_start,
                'date_stop': fy_date_stop,
                'init': init_flag})
            fy_date_start = fy_date_stop + relativedelta(days=1)
            try:
                fy_id = fy_obj.find(cr, uid, fy_date_start, context=context)
                init_flag = False
            except:
                fy_id = False
            if fy_id:
                fy = fy_obj.browse(cr, uid, fy_id)
                if fy.state == 'done':
                    init_flag = True
                fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
            else:
                fy_date_stop = fy_date_stop + relativedelta(years=1)

        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')
        amount_to_depr = residual_amount = asset.asset_value

        # step 1: calculate depreciation amount per fiscal year
        fy_residual_amount = residual_amount
        i_max = len(table) - 1
        asset_sign = asset.asset_value >= 0 and 1 or -1
        for i, entry in enumerate(table):
            year_amount = self._compute_year_amount(
                cr, uid, asset, amount_to_depr,
                fy_residual_amount, context=context)
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
                    cr, uid, entry, asset, firstyear, context=context)
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
                raise orm.except_orm(
                    _('Programming Error!'),
                    _("Illegal value %s in asset.method_period.")
                    % asset.method_period)
            for line in lines:
                line['depreciated_value'] = amount_to_depr - residual_amount
                residual_amount -= line['amount']
                line['remaining_value'] = residual_amount
            entry['lines'] = lines

        return table

    def _get_depreciation_entry_name(self, cr, uid, asset, seq, context=None):
        """ use this method to customise the name of the accounting entry """
        return (asset.code or str(asset.id)) + '/' + str(seq)

    def compute_depreciation_board(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        context = context.copy()
        depreciation_lin_obj = self.pool.get(
            'account.asset.depreciation.line')
        digits = self.pool.get('decimal.precision').precision_get(
            cr, uid, 'Account')

        for asset in self.browse(cr, uid, ids, context=context):
            if asset.value_residual == 0.0:
                continue
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                '|', ('move_check', '=', True), ('init_entry', '=', True)]
            posted_depreciation_line_ids = depreciation_lin_obj.search(
                cr, uid, domain, order='line_date desc')
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_line = depreciation_lin_obj.browse(
                    cr, uid, posted_depreciation_line_ids[0], context=context)
            else:
                last_depreciation_line = False
            domain = [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                ('move_id', '=', False),
                ('init_entry', '=', False)]
            old_depreciation_line_ids = depreciation_lin_obj.search(
                cr, uid, domain)
            if old_depreciation_line_ids:
                depreciation_lin_obj.unlink(
                    cr, uid, old_depreciation_line_ids, context=context)
            context['company_id'] = asset.company_id.id

            table = self._compute_depreciation_table(
                cr, uid, asset, context=context)
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
            if (len(posted_depreciation_line_ids) > 0):
                last_depreciation_date = datetime.strptime(
                    last_depreciation_line.line_date, '%Y-%m-%d')
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_depreciation_date:
                    raise orm.except_orm(
                        _('Error!'),
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
                cr.execute(
                    "SELECT COALESCE(SUM(amount), 0.0) "
                    "FROM account_asset_depreciation_line "
                    "WHERE id IN %s",
                    (tuple(posted_depreciation_line_ids),))
                res = cr.fetchone()
                depreciated_value = res[0]
                residual_amount = asset.asset_value - depreciated_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    entry = table[table_i_start]
                    cr.execute(
                        "SELECT COALESCE(SUM(amount), 0.0) "
                        "FROM account_asset_depreciation_line "
                        "WHERE id in %s "
                        "      AND line_date >= %s and line_date <= %s",
                        (tuple(posted_depreciation_line_ids),
                         entry['date_start'],
                         entry['date_stop']))
                    res = cr.fetchone()
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
                    name = self._get_depreciation_entry_name(
                        cr, uid, asset, seq, context=context)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        cr.execute(
                            "SELECT COALESCE(SUM(amount), 0.0) "
                            "FROM account_asset_depreciation_line "
                            "WHERE type = 'depreciate' AND line_date < %s "
                            "AND asset_id = %s ",
                            (last_date, asset.id))
                        res = cr.fetchone()
                        amount = asset.asset_value - res[0]
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
                    depr_line_id = depreciation_lin_obj.create(
                        cr, uid, vals, context=context)
                line_i_start = 0

        return True

    def validate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        currency_obj = self.pool.get('res.currency')
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.type == 'normal' and currency_obj.is_zero(
                    cr, uid, asset.company_id.currency_id,
                    asset.value_residual):
                asset.write({'state': 'close'}, context=context)
            else:
                asset.write({'state': 'open'}, context=context)
        return True

    def remove(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context):
            ctx = dict(context, active_ids=ids, active_id=ids[0])
            if asset.value_residual:
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

    def set_to_draft(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'draft'}, context=context)

    def _asset_value_compute(self, cr, uid, asset, context=None):
        if asset.type == 'view':
            asset_value = 0.0
        else:
            asset_value = asset.purchase_value - asset.salvage_value
        return asset_value

    def _asset_value(self, cr, uid, ids, name, args, context=None):
        res = {}
        for asset in self.browse(cr, uid, ids, context):
            if asset.type == 'normal':
                res[asset.id] = self._asset_value_compute(
                    cr, uid, asset, context)
            else:
                def _value_get(record):
                    asset_value = self._asset_value_compute(
                        cr, uid, asset, context)
                    for rec in record.child_ids:
                        asset_value += \
                            rec.type == 'normal' and \
                            self._asset_value_compute(cr, uid, rec, context) \
                            or _value_get(rec)
                    return asset_value
                res[asset.id] = _value_get(asset)
        return res

    def _compute_depreciation(self, cr, uid, ids, name, args, context=None):
        res = {}
        for asset in self.browse(cr, uid, ids, context=context):
            res[asset.id] = {}
            child_ids = self.search(cr, uid,
                                    [('parent_id', 'child_of', [asset.id]),
                                     ('type', '=', 'normal')],
                                    context=context)
            if child_ids:
                cr.execute(
                    "SELECT COALESCE(SUM(amount),0.0) AS amount "
                    "FROM account_asset_depreciation_line "
                    "WHERE asset_id in %s "
                    "AND type in ('depreciate','remove') "
                    "AND (init_entry=TRUE OR move_check=TRUE)",
                    (tuple(child_ids),))
                value_depreciated = cr.fetchone()[0]
            else:
                value_depreciated = 0.0
            res[asset.id]['value_residual'] = \
                asset.asset_value - value_depreciated
            res[asset.id]['value_depreciated'] = \
                value_depreciated
        return res

    def _move_line_check(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for asset in self.browse(cr, uid, ids, context=context):
            for line in asset.depreciation_line_ids:
                if line.move_id:
                    res[asset.id] = True
                    continue
        return res

    def onchange_purchase_salvage_value(
            self, cr, uid, ids, purchase_value,
            salvage_value, date_start, context=None):
        if not context:
            context = {}
        val = {}
        purchase_value = purchase_value or 0.0
        salvage_value = salvage_value or 0.0
        if purchase_value or salvage_value:
            val['asset_value'] = purchase_value - salvage_value
        if ids:
            aadl_obj = self.pool.get('account.asset.depreciation.line')
            dl_create_ids = aadl_obj.search(
                cr, uid, [('type', '=', 'create'), ('asset_id', 'in', ids)])
            aadl_obj.write(
                cr, uid, dl_create_ids,
                {'amount': val['asset_value'], 'line_date': date_start})
        return {'value': val}

    def _get_assets(self, cr, uid, ids, context=None):
        asset_ids = []
        for asset in self.browse(cr, uid, ids, context=context):
            def _parent_get(record):
                asset_ids.append(record.id)
                if record.parent_id:
                    _parent_get(record.parent_id)
            _parent_get(asset)
        return asset_ids

    def _get_assets_from_dl(self, cr, uid, ids, context=None):
        asset_ids = []
        for dl in filter(
                lambda x: x.type in ['depreciate', 'remove'] and
                        (x.init_entry or x.move_id),
                self.pool.get('account.asset.depreciation.line').browse(
                    cr, uid, ids, context=context)):
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

    def _get_method(self, cr, uid, context=None):
        return self.pool.get('account.asset.category')._get_method(
            cr, uid, context)

    def _get_method_time(self, cr, uid, context=None):
        return self.pool.get('account.asset.category')._get_method_time(
            cr, uid, context)

    def _get_company(self, cr, uid, context=None):
        return self.pool.get('res.company')._company_default_get(
            cr, uid, 'account.asset.asset', context=context)

    _columns = {
        'account_move_line_ids': fields.one2many(
            'account.move.line', 'asset_id', 'Entries', readonly=True),
        'move_line_check': fields.function(
            _move_line_check, method=True, type='boolean',
            string='Has accounting entries'),
        'name': fields.char(
            'Asset Name', size=64, required=True,
            readonly=True, states={'draft': [('readonly', False)]}),
        'code': fields.char(
            'Reference', size=32, readonly=True,
            states={'draft': [('readonly', False)]}),
        'purchase_value': fields.float(
            'Purchase Value', required=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="\nThe Asset Value is calculated as follows:"
                 "\nPurchase Value - Salvage Value."),
        'asset_value': fields.function(
            _asset_value, method=True,
            digits_compute=dp.get_precision('Account'),
            string='Asset Value',
            store={
                'account.asset.asset': (
                    _get_assets,
                    ['purchase_value', 'salvage_value', 'parent_id'], 10),
            },
            help="This amount represent the initial value of the asset."),
        'value_residual': fields.function(
            _compute_depreciation, method=True, multi='cd',
            digits_compute=dp.get_precision('Account'),
            string='Residual Value',
            store={
                'account.asset.asset': (
                    _get_assets, [
                        'purchase_value', 'salvage_value',
                        'parent_id', 'depreciation_line_ids'
                    ], 20),
                'account.asset.depreciation.line': (
                    _get_assets_from_dl,
                    ['amount', 'init_entry', 'move_id'], 20),
            }),
        'value_depreciated': fields.function(
            _compute_depreciation, method=True, multi='cd',
            digits_compute=dp.get_precision('Account'),
            string='Depreciated Value',
            store={
                'account.asset.asset': (
                    _get_assets, [
                        'purchase_value', 'salvage_value',
                        'parent_id', 'depreciation_line_ids'
                    ], 30),
                'account.asset.depreciation.line': (
                    _get_assets_from_dl,
                    ['amount', 'init_entry', 'move_id'], 30),
            }),
        'salvage_value': fields.float(
            'Salvage Value', digits_compute=dp.get_precision('Account'),
            readonly=True,
            states={'draft': [('readonly', False)]},
            help="The estimated value that an asset will realize upon "
                 "its sale at the end of its useful life.\n"
                 "This value is used to determine the depreciation amounts."),
        'note': fields.text('Note'),
        'category_id': fields.many2one(
            'account.asset.category', 'Asset Category',
            change_default=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'parent_id': fields.many2one(
            'account.asset.asset', 'Parent Asset', readonly=True,
            states={'draft': [('readonly', False)]},
            domain=[('type', '=', 'view')],
            ondelete='restrict'),
        'parent_left': fields.integer('Parent Left', select=1),
        'parent_right': fields.integer('Parent Right', select=1),
        'child_ids': fields.one2many(
            'account.asset.asset', 'parent_id', 'Child Assets'),
        'date_start': fields.date(
            'Asset Start Date', readonly=True,
            states={'draft': [('readonly', False)]},
            help="You should manually add depreciation lines "
                 "with the depreciations of previous fiscal years "
                 "if the Depreciation Start Date is different from the date "
                 "for which accounting entries need to be generated."),
        'date_remove': fields.date('Asset Removal Date', readonly=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('open', 'Running'),
            ('close', 'Close'),
            ('removed', 'Removed'),
            ], 'Status', required=True,
            help="When an asset is created, the status is 'Draft'.\n"
                 "If the asset is confirmed, the status goes in 'Running' "
                 "and the depreciation lines can be posted "
                 "to the accounting.\n"
                 "If the last depreciation line is posted, "
                 "the asset goes into the 'Close' status.\n"
                 "When the removal entries are generated, "
                 "the asset goes into the 'Removed' status."),
        'active': fields.boolean('Active'),
        'partner_id': fields.many2one(
            'res.partner', 'Partner', readonly=True,
            states={'draft': [('readonly', False)]}),
        'method': fields.selection(
            _get_method, 'Computation Method',
            required=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="Choose the method to use to compute "
                 "the amount of depreciation lines.\n"
                 "  * Linear: Calculated on basis of: "
                 "Gross Value / Number of Depreciations\n"
                 "  * Degressive: Calculated on basis of: "
                 "Residual Value * Degressive Factor"
                 "  * Degressive-Linear (only for Time Method = Year): "
                 "Degressive becomes linear when the annual linear "
                 "depreciation exceeds the annual degressive depreciation"),
        'method_number': fields.integer(
            'Number of Years', readonly=True,
            states={'draft': [('readonly', False)]},
            help="The number of years needed to depreciate your asset"),
        'method_period': fields.selection([
            ('month', 'Month'),
            ('quarter', 'Quarter'),
            ('year', 'Year'),
            ], 'Period Length',
            required=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="Period length for the depreciation accounting entries"),
        'method_end': fields.date(
            'Ending Date', readonly=True,
            states={'draft': [('readonly', False)]}),
        'method_progress_factor': fields.float(
            'Degressive Factor', readonly=True,
            states={'draft': [('readonly', False)]}),
        'method_time': fields.selection(
            _get_method_time, 'Time Method',
            required=True, readonly=True,
            states={'draft': [('readonly', False)]},
            help="Choose the method to use to compute the dates and "
                 "number of depreciation lines.\n"
                 "  * Number of Years: Specify the number of years "
                 "for the depreciation.\n"
                 # "  * Number of Depreciations: Fix the number of "
                 # "depreciation lines and the time between 2 depreciations.\n"
                 # "  * Ending Date: Choose the time between 2 depreciations "
                 # "and the date the depreciations won't go beyond."
            ),
        'prorata': fields.boolean(
            'Prorata Temporis', readonly=True,
            states={'draft': [('readonly', False)]},
            help="Indicates that the first depreciation entry for this asset "
                 "have to be done from the depreciation start date instead "
                 "of the first day of the fiscal year."),
        'history_ids': fields.one2many(
            'account.asset.history', 'asset_id',
            'History', readonly=True),
        'depreciation_line_ids': fields.one2many(
            'account.asset.depreciation.line', 'asset_id',
            'Depreciation Lines',
            readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection([
            ('view', 'View'),
            ('normal', 'Normal'),
            ], 'Type',
            required=True, readonly=True,
            states={'draft': [('readonly', False)]}),
        'company_id': fields.many2one(
            'res.company', 'Company', required=True, readonly=True),
        'company_currency_id': fields.related(
            'company_id', 'currency_id',
            string='Company Currency',
            type='many2one',
            relation='res.currency',
            store=True, readonly=True,),
        'account_analytic_id': fields.many2one(
            'account.analytic.account', 'Analytic account',
            domain=[('type', '!=', 'view'),
                    ('state', 'not in', ('close', 'cancelled'))]),
    }

    _defaults = {
        'date_start': lambda obj, cr, uid, context: time.strftime('%Y-%m-%d'),
        'active': True,
        'state': 'draft',
        'method': 'linear',
        'method_number': 5,
        'method_time': 'year',
        'method_period': 'year',
        'method_progress_factor': 0.3,
        'type': 'normal',
        'company_id': _get_company,
    }

    def _check_recursion(self, cr, uid, ids,
                         context=None, parent=None):
        return super(account_asset_asset, self)._check_recursion(
            cr, uid, ids, context=context, parent=parent)

    def _check_method(self, cr, uid, ids, context=None):
        for asset in self.browse(cr, uid, ids, context=context):
            if asset.method == 'degr-linear' and asset.method_time != 'year':
                return False
        return True

    _constraints = [
        (_check_recursion,
         "Error ! You can not create recursive assets.", ['parent_id']),
        (_check_method,
         "Degressive-Linear is only supported for Time Method = Year.",
         ['method']),
    ]

    def onchange_type(self, cr, uid, ids, asset_type, context=None):
        res = {'value': {}}
        if asset_type == 'view':
            res['value'] = {
                'date_start': False,
                'category_id': False,
                'purchase_value': 0.0,
                'salvage_value': 0.0,
                'code': False,
            }
        for asset in self.browse(cr, uid, ids, context):
            if asset.depreciation_line_ids:
                self.pool.get('account.asset.depreciation.line').unlink(
                    cr, uid,
                    [x.id for x in asset.depreciation_line_ids], context)
        return res

    def onchange_category_id(self, cr, uid, ids, category_id, context=None):
        for asset in self.browse(cr, uid, ids, context):
            for line in asset.depreciation_line_ids:
                if line.move_id:
                    raise orm.except_orm(
                        _('Error!'),
                        _("You cannot change the category of an asset "
                          "with accounting entries."))
        res = {'value': {}}
        asset_categ_obj = self.pool.get('account.asset.category')
        if category_id:
            category_obj = asset_categ_obj.browse(
                cr, uid, category_id, context=context)
            res['value'] = {
                'parent_id': category_obj.parent_id.id,
                'method': category_obj.method,
                'method_number': category_obj.method_number,
                'method_time': category_obj.method_time,
                'method_period': category_obj.method_period,
                'method_progress_factor': category_obj.method_progress_factor,
                'prorata': category_obj.prorata,
                'account_analytic_id': category_obj.account_analytic_id.id,
            }
        return res

    def onchange_method_time(self, cr, uid, ids,
                             method_time='number', context=None):
        res = {'value': {}}
        if method_time != 'year':
            res['value'] = {'prorata': True}
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default.update({
            'depreciation_line_ids': [],
            'account_move_line_ids': [],
            'state': 'draft',
            'history_ids': []})
        return super(account_asset_asset, self).copy(
            cr, uid, id, default, context=context)

    def _compute_entries(self, cr, uid, ids, period_id,
                         check_triggers=False, context=None):
        # To DO : add ir_cron job calling this method to
        # generate periodical accounting entries
        if context is None:
            context = {}
        result = []
        period_obj = self.pool.get('account.period')
        depreciation_obj = self.pool.get('account.asset.depreciation.line')
        period = period_obj.browse(cr, uid, period_id, context=context)
        if check_triggers:
            recompute_obj = self.pool.get('account.asset.recompute.trigger')
            recompute_ids = recompute_obj.search(
                cr, SUPERUSER_ID, [('state', '=', 'open')])
            if recompute_ids:
                recompute_triggers = recompute_obj.read(
                    cr, uid, recompute_ids, ['company_id'])

        assets = self.browse(cr, uid, ids, context=context)
        for asset in assets:
            depreciation_ids = depreciation_obj.search(cr, uid, [
                ('asset_id', '=', asset.id),
                ('type', '=', 'depreciate'),
                ('init_entry', '=', False),
                ('line_date', '<', period.date_start),
                ('move_check', '=', False)], context=context)
            if depreciation_ids:
                for line in depreciation_obj.browse(
                        cr, uid, depreciation_ids):
                    asset_ref = asset.code and '%s (ref: %s)' \
                        % (asset.name, asset.code) or asset.name
                    raise orm.except_orm(
                        _('Error!'),
                        _("Asset '%s' contains unposted lines "
                          "prior to the selected period."
                          "\nPlease post these entries first !") % asset_ref)
            if check_triggers and recompute_ids:
                triggers = filter(
                    lambda x: x['company_id'][0] == asset.company_id.id,
                    recompute_triggers)
                if triggers:
                    self.compute_depreciation_board(
                        cr, uid, [asset.id], context=context)
        depreciation_ids = depreciation_obj.search(cr, uid, [
            ('asset_id', 'in', ids),
            ('type', '=', 'depreciate'),
            ('init_entry', '=', False),
            ('line_date', '<=', period.date_stop),
            ('line_date', '>=', period.date_start),
            ('move_check', '=', False)], context=context)
        for depreciation in depreciation_obj.browse(
                cr, uid, depreciation_ids, context=context):
            context.update({'depreciation_date': depreciation.line_date})
            result += depreciation_obj.create_move(
                cr, uid, [depreciation.id], context=context)

        if check_triggers and recompute_ids:
            asset_company_ids = set([x.company_id.id for x in assets])
            triggers = filter(
                lambda x: x['company_id'][0] in asset_company_ids,
                recompute_triggers)
            if triggers:
                recompute_vals = {
                    'date_completed': time.strftime(
                        tools.DEFAULT_SERVER_DATETIME_FORMAT),
                    'state': 'done',
                }
                trigger_ids = [x['id'] for x in triggers]
                recompute_obj.write(
                    cr, SUPERUSER_ID, trigger_ids, recompute_vals)

        return result

    def create(self, cr, uid, vals, context=None):
        if not context:
            context = {}
        if vals.get('method_time') != 'year' and not vals.get('prorata'):
            vals['prorata'] = True
        asset_id = super(account_asset_asset, self).create(
            cr, uid, vals, context=context)
        if context.get('create_asset_from_move_line'):
            # Trigger compute of asset_value
            self.write(cr, uid, [asset_id], {'salvage_value': 0.0})
        asset = self.browse(cr, uid, asset_id, context)
        if asset.type == 'normal':
            # create first asset line
            asset_line_obj = self.pool.get('account.asset.depreciation.line')
            line_name = self._get_depreciation_entry_name(
                cr, uid, asset, 0, context=context)
            asset_line_vals = {
                'amount': asset.asset_value,
                'asset_id': asset_id,
                'name': line_name,
                'line_date': asset.date_start,
                'init_entry': True,
                'type': 'create',
            }
            asset_line_id = asset_line_obj.create(
                cr, uid, asset_line_vals, context=context)
            if context.get('create_asset_from_move_line'):
                asset_line_obj.write(
                    cr, uid, [asset_line_id], {'move_id': context['move_id']})
        return asset_id

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        if vals.get('method_time'):
            if vals['method_time'] != 'year' and not vals.get('prorata'):
                vals['prorata'] = True
        for asset in self.browse(cr, uid, ids, context):
            asset_type = vals.get('type') or asset.type
            super(account_asset_asset, self).write(
                cr, uid, [asset.id], vals, context)
            if asset_type == 'view' or \
                    context.get('asset_validate_from_write'):
                continue
            if asset.category_id.open_asset and \
                    context.get('create_asset_from_move_line'):
                self.compute_depreciation_board(
                    cr, uid, [asset.id], context=context)
                # extra context to avoid recursion
                self.validate(
                    cr, uid, [asset.id],
                    context=dict(context, asset_validate_from_write=True))
        return True

    def open_entries(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        cr.execute("SELECT move_id, date FROM account_move_line "
                   "WHERE asset_id IN %s ORDER BY date ASC", (tuple(ids),))
        res = cr.fetchall()
        am_ids = [x[0] for x in res]
        return {
            'name': _("Journal Entries"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
            'nodestroy': True,
            'domain': [('id', 'in', am_ids)],
        }

    def open_move_lines(self, cr, uid, ids, context=None):
        cr.execute(
            "SELECT aml2.id FROM account_move_line aml "
            "INNER JOIN account_move am ON am.id=aml.move_id "
            "INNER JOIN account_move_line aml2 ON aml2.move_id = am.id "
            "WHERE aml.asset_id IN %s",
            (tuple(ids),))
        res = cr.fetchall()
        aml_ids = [x[0] for x in res]
        return {
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'context': context,
            'nodestroy': True,
            'domain': [('id', 'in', aml_ids)],
        }


class account_asset_depreciation_line(orm.Model):
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    def _compute(self, cr, uid, ids, name, args, context=None):
        res = {}
        dlines = self.browse(cr, uid, ids)
        if not dlines:
            return res
        asset_value = dlines[0].asset_id.asset_value
        dlines = filter(lambda x: x.type == 'depreciate', dlines)
        dlines = sorted(dlines, key=lambda dl: dl.line_date)

        for i, dl in enumerate(dlines):
            if i == 0:
                depreciated_value = dl.previous_id and \
                    (asset_value - dl.previous_id.remaining_value) or 0.0
                remaining_value = asset_value - depreciated_value - dl.amount
            else:
                depreciated_value += dl.previous_id.amount
                remaining_value -= dl.amount
            res[dl.id] = {
                'depreciated_value': depreciated_value,
                'remaining_value': remaining_value,
            }
        return res

    def _move_check(self, cr, uid, ids, name, args, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = bool(line.move_id)
        return res

    def _get_dl(self, cr, uid, ids, context=None):
        assets = []
        for dl in filter(
                lambda x: x.type == 'depreciate',
                self.browse(cr, uid, ids, context=context)):
            assets.append(dl.asset_id)
        assets = set(assets)
        result = []
        for asset in assets:
            result += [x.id for x in asset.depreciation_line_ids]
        return result

    _order = 'type, line_date'
    _columns = {
        'name': fields.char('Depreciation Name', size=64, readonly=True),
        'asset_id': fields.many2one(
            'account.asset.asset', 'Asset',
            required=True, ondelete='cascade'),
        'previous_id': fields.many2one(
            'account.asset.depreciation.line', 'Previous Depreciation Line',
            readonly=True),
        'parent_state': fields.related(
            'asset_id', 'state', type='char', string='State of Asset'),
        'asset_value': fields.related(
            'asset_id', 'asset_value', type='float', string='Asset Value'),
        'amount': fields.float(
            'Amount', digits_compute=dp.get_precision('Account'),
            required=True),
        'remaining_value': fields.function(
            _compute,
            method=True,
            digits_compute=dp.get_precision('Account'),
            string='Next Period Depreciation',
            store={
                'account.asset.depreciation.line': (_get_dl, ['amount'], 10),
            },
            multi='all'),
        'depreciated_value': fields.function(
            _compute,
            method=True,
            digits_compute=dp.get_precision('Account'),
            string='Amount Already Depreciated',
            store={
                'account.asset.depreciation.line': (_get_dl, ['amount'], 10),
            },
            multi='all'),
        'line_date': fields.date('Date', required=True),
        'move_id': fields.many2one(
            'account.move', 'Depreciation Entry', readonly=True),
        'move_check': fields.function(
            _move_check,
            method=True,
            type='boolean',
            string='Posted',
            store={
                'account.asset.depreciation.line': (
                    lambda self, cr, uid, ids, c={}: ids, ['move_id'], 10),
            }),
        'type': fields.selection([
            ('create', 'Asset Value'),
            ('depreciate', 'Depreciation'),
            ('remove', 'Asset Removal'),
            ], 'Type', readonly=True),
        'init_entry': fields.boolean(
            'Initial Balance Entry',
            help="Set this flag for entries of previous fiscal years "
                 "for which OpenERP has not generated accounting entries."),
    }

    _defaults = {
        'type': 'depreciate',
    }

    def onchange_amount(self, cr, uid, ids, dl_type, asset_value,
                        amount, depreciated_value, context=None):
        res = {}
        if dl_type == 'depreciate':
            res['value'] = {
                'remaining_value': asset_value - depreciated_value - amount}
        return res

    def unlink(self, cr, uid, ids, context=None):
        for dl in self.browse(cr, uid, ids, context):
            if dl.type == 'create':
                raise orm.except_orm(
                    _('Error!'),
                    _("You cannot remove an asset line "
                      "of type 'Asset Value'."))
            elif dl.move_id:
                raise orm.except_orm(
                    _('Error!'),
                    _("You cannot delete a depreciation line with "
                      "an associated accounting entry."))
            previous_id = dl.previous_id and dl.previous_id.id or False
            cr.execute(
                "SELECT id FROM account_asset_depreciation_line "
                "WHERE previous_id = %s" % dl.id)
            next = cr.fetchone()
            if next:
                next_id = next[0]
                self.write(cr, uid, [next_id], {'previous_id': previous_id})
        return super(account_asset_depreciation_line, self).unlink(
            cr, uid, ids, context=context)

    def write(self, cr, uid, ids, vals, context=None):
        if not context:
            context = {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        for dl in self.browse(cr, uid, ids, context):
            if vals.keys() == ['move_id'] and not vals['move_id']:
                # allow to remove an accounting entry via the
                # 'Delete Move' button on the depreciation lines.
                if not context.get('unlink_from_asset'):
                    raise orm.except_orm(
                        _('Error!'),
                        _("You are not allowed to remove an accounting entry "
                          "linked to an asset."
                          "\nYou should remove such entries from the asset."))
            elif vals.keys() == ['asset_id']:
                continue
            elif dl.move_id and not context.get('allow_asset_line_update'):
                raise orm.except_orm(
                    _('Error!'),
                    _("You cannot change a depreciation line "
                      "with an associated accounting entry."))
            elif vals.get('init_entry'):
                cr.execute(
                    "SELECT id "
                    "FROM account_asset_depreciation_line "
                    "WHERE asset_id = %s AND move_check = TRUE "
                    "AND type = 'depreciate' AND line_date <= %s LIMIT 1",
                    (dl.asset_id.id, dl.line_date))
                res = cr.fetchone()
                if res:
                    raise orm.except_orm(
                        _('Error!'),
                        _("You cannot set the 'Initial Balance Entry' flag "
                          "on a depreciation line "
                          "with prior posted entries."))
            elif vals.get('line_date'):
                cr.execute(
                    "SELECT id "
                    "FROM account_asset_depreciation_line "
                    "WHERE asset_id = %s "
                    "AND (init_entry=TRUE OR move_check=TRUE)"
                    "AND line_date > %s LIMIT 1",
                    (dl.asset_id.id, vals['line_date']))
                res = cr.fetchone()
                if res:
                    raise orm.except_orm(
                        _('Error!'),
                        _("You cannot set the date on a depreciation line "
                          "prior to already posted entries."))
        return super(account_asset_depreciation_line, self).write(
            cr, uid, ids, vals, context)

    def _setup_move_data(self, depreciation_line, depreciation_date,
                         period_id, context):
        asset = depreciation_line.asset_id
        move_data = {
            'name': asset.name,
            'date': depreciation_date,
            'ref': depreciation_line.name,
            'period_id': period_id,
            'journal_id': asset.category_id.journal_id.id,
        }
        return move_data

    def _setup_move_line_data(self, depreciation_line, depreciation_date,
                              period_id, account_id, type, move_id, context):
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
            'move_id': move_id,
            'account_id': account_id,
            'credit': credit,
            'debit': debit,
            'period_id': period_id,
            'journal_id': asset.category_id.journal_id.id,
            'partner_id': asset.partner_id.id,
            'analytic_account_id': analytic_id,
            'date': depreciation_date,
            'asset_id': asset.id,
        }
        return move_line_data

    def create_move(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        asset_obj = self.pool.get('account.asset.asset')
        period_obj = self.pool.get('account.period')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        created_move_ids = []
        asset_ids = []
        for line in self.browse(cr, uid, ids, context=context):
            asset = line.asset_id
            if asset.method_time == 'year':
                depreciation_date = context.get('depreciation_date') or \
                    line.line_date
            else:
                depreciation_date = context.get('depreciation_date') or \
                    time.strftime('%Y-%m-%d')
            ctx = dict(context, account_period_prefer_normal=True)
            period_ids = period_obj.find(
                cr, uid, depreciation_date, context=ctx)
            period_id = period_ids and period_ids[0] or False
            move_id = move_obj.create(cr, uid, self._setup_move_data(
                line, depreciation_date, period_id, context),
                context=context)
            depr_acc_id = asset.category_id.account_depreciation_id.id
            exp_acc_id = asset.category_id.account_expense_depreciation_id.id
            ctx = dict(context, allow_asset=True)
            move_line_obj.create(cr, uid, self._setup_move_line_data(
                line, depreciation_date, period_id, depr_acc_id,
                'depreciation', move_id, context), ctx)
            move_line_obj.create(cr, uid, self._setup_move_line_data(
                line, depreciation_date, period_id, exp_acc_id, 'expense',
                move_id, context), ctx)
            self.write(
                cr, uid, line.id, {'move_id': move_id},
                context={'allow_asset_line_update': True})
            created_move_ids.append(move_id)
            asset_ids.append(asset.id)
        # we re-evaluate the assets to determine whether we can close them
        for asset in asset_obj.browse(
                cr, uid, list(set(asset_ids)), context=context):
            if currency_obj.is_zero(cr, uid, asset.company_id.currency_id,
                                    asset.value_residual):
                asset.write({'state': 'close'})
        return created_move_ids

    def open_move(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            return {
                'name': _("Journal Entry"),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'context': context,
                'nodestroy': True,
                'domain': [('id', '=', line.move_id.id)],
            }

    def unlink_move(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        move_obj = self.pool.get('account.move')
        ctx = {'unlink_from_asset': True}
        for line in self.browse(cr, uid, ids, context=context):
            move = line.move_id
            if move.state == 'posted':
                move_obj.button_cancel(cr, uid, [move.id], context=context)
            move_obj.unlink(cr, uid, [move.id], context=ctx)
            # trigger store function
            self.write(cr, uid, [line.id], {'move_id': False}, context=ctx)
            if line.parent_state == 'close':
                line.asset_id.write({'state': 'open'})
            elif line.parent_state == 'removed' and line.type == 'remove':
                line.asset_id.write({'state': 'close'})
                self.unlink(cr, uid, [line.id])
        return True


class account_move_line(orm.Model):
    _inherit = 'account.move.line'
    _columns = {
        'asset_id': fields.many2one(
            'account.asset.asset', 'Asset', ondelete="restrict"),
    }


class account_asset_history(orm.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _columns = {
        'name': fields.char('History name', size=64, select=1),
        'user_id': fields.many2one('res.users', 'User', required=True),
        'date': fields.date('Date', required=True),
        'asset_id': fields.many2one(
            'account.asset.asset', 'Asset', required=True, ondelete='cascade'),
        'method_time': fields.selection([
            ('year', 'Number of Years'),
            # ('number','Number of Depreciations'),
            # ('end','Ending Date'),
            ], 'Time Method', required=True),
        'method_number': fields.integer(
            'Number of Years',
            help="The number of years needed to depreciate your asset"),
        'method_period': fields.selection([
            ('month', 'Month'),
            ('quarter', 'Quarter'),
            ('year', 'Year'),
            ], 'Period Length',
            help="Period length for the depreciation accounting entries"),
        'method_end': fields.date('Ending date'),
        'note': fields.text('Note'),
    }
    _order = 'date desc'
    _defaults = {
        'date': lambda *args: time.strftime('%Y-%m-%d'),
        'user_id': lambda self, cr, uid, ctx: uid
    }
