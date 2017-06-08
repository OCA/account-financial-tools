# -*- coding: utf-8 -*-
# © 2014 ONESTEiN BV (<http://www.onestein.eu>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import calendar
from openerp import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import openerp.addons.decimal_precision as dp


class DummyFy(object):
    def __init__(self, *args, **argv):
        for key, arg in argv.items():
            setattr(self, key, arg)


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    spread_date = fields.Date(string='Alternative Start Date')
    period_number = fields.Integer(
        string='Number of Periods',
        default=12,
        help="Number of Periods",
        required=True)
    period_type = fields.Selection([
        ('month', 'Month'),
        ('quarter', 'Quarter'),
        ('year', 'Year'),
        ], string='Period Type',
        default='month',
        help="Period length for the entries",
        required=True)
    spread_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Spread Account')
    remaining_amount = fields.Float(
        string='Residual Amount',
        digits=dp.get_precision('Account'))
    spreaded_amount = fields.Float(
        string='Spread Amount',
        digits=dp.get_precision('Account'))
    spread_line_ids = fields.One2many(
        comodel_name='account.invoice.spread.line',
        inverse_name='invoice_line_id',
        string='Spread Lines')

    @api.multi
    def spread_details(self):
        """Button on the invoice lines tree view on the invoice
        form to show the spread form view."""
        view_obj = self.env['ir.ui.view'].search(
            [('name', '=', 'account.invoice.line.spread')])
        view_id = False
        if view_obj:
            view_id = view_obj.id

        view = {
            'name': _('Spread Details'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.line',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'readonly': False,
            'res_id': self.id,
            }
        return view

    @api.model
    def move_line_get_item(self, line):
        res = super(AccountInvoiceLine, self).move_line_get_item(line)
        if line.spread_account_id:
            res.update({'account_id': line.spread_account_id.id})
        return res

    @api.model
    @api.returns('account.period', lambda r: r.id)
    def _get_period(self):
        period = self.env['account.period'].with_context(
            account_period_prefer_normal=True).find()
        if period:
            if len(period) > 1:
                return period[0]
            else:
                return period
        return self.env['account.period']

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
            "FROM account_fiscalyear WHERE id=%s" % fy_id)
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
                        duration = (datetime(year, 12, 31) -
                                    fy_date_start).days + 1
                    factor = float(duration) / cy_days
                elif i == cnt - 1:  # last year
                    duration = fy_date_stop - datetime(year, 01, 01)
                    duration_days = duration.days + 1
                    factor += float(duration_days) / cy_days
                else:
                    factor += 1.0
                year += 1
            return factor

    def _get_fy_duration_factor(self, entry, line, firstyear):

        duration_factor = 1.0
        fy_id = entry['fy_id']

        if firstyear:
            spread_date_start = datetime.strptime(
                line.invoice_id.date_invoice, '%Y-%m-%d')
            fy_date_stop = entry['date_stop']
            first_fy_spread_days = \
                (fy_date_stop - spread_date_start).days + 1
            if fy_id:
                first_fy_duration = self._get_fy_duration(fy_id, option='days')
                first_fy_year_factor = self._get_fy_duration(
                    fy_id, option='years'
                )
                duration_factor = \
                    float(first_fy_spread_days) / first_fy_duration \
                    * first_fy_year_factor
            else:
                first_fy_duration = \
                    calendar.isleap(entry['date_start'].year) \
                    and 366 or 365
                duration_factor = \
                    float(first_fy_spread_days) / first_fy_duration
        elif fy_id:
            duration_factor = self._get_fy_duration(fy_id, option='years')

        return duration_factor

    @api.model
    def _get_spread_start_date(self, line, fy):

        if line.spread_date:
            spread_start_date = datetime.strptime(line.spread_date, '%Y-%m-%d')
        elif line.invoice_id.date_invoice:
            spread_start_date = datetime.strptime(
                line.invoice_id.date_invoice, '%Y-%m-%d')
        else:
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            spread_start_date = datetime(
                fy_date_start.year, fy_date_start.month, 1
            )
        return spread_start_date

    @api.model
    def _get_spread_stop_date(self, line, spread_start_date):
        if line.period_type == 'month':
            spread_stop_date = spread_start_date + relativedelta(
                months=line.period_number, days=-1)
        elif line.period_type == 'quarter':
            spread_stop_date = spread_start_date + relativedelta(
                months=line.period_number * 3, days=-1)
        elif line.period_type == 'year':
            spread_stop_date = spread_start_date + relativedelta(
                years=line.period_number, days=-1)
        return spread_stop_date

    @api.model
    def _compute_year_amount(self, line):
        if line.period_type == 'month':
            factor = line.period_number / 12.0
        elif line.period_type == 'quarter':
            factor = line.period_number * 3 / 12.0
        elif line.period_type == 'year':
            factor = line.period_number

        period_amount = line.price_subtotal / factor

        return period_amount

    def _compute_spread_table(self, invline):

        table = []
        if not invline.period_number or \
                not invline.spread_account_id or \
                not invline.period_type:
            return table

        fy_obj = self.env['account.fiscalyear']
        init_flag = False
        try:
            fy_id = fy_obj.find(invline.invoice_id.date_invoice)
            fy = fy_obj.browse(fy_id)
            if fy.state == 'done':
                init_flag = True
            fy_date_start = datetime.strptime(fy.date_start, '%Y-%m-%d')
            fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
        except:
            # The following logic is used when no fiscalyear
            # is defined for the invoice start date:
            # - We lookup the first fiscal year defined in the system
            # - The 'undefined' fiscal years are assumed to be years
            # with a duration equals to calendar year
            self.env.cr.execute(
                "SELECT id, date_start, date_stop "
                "FROM account_fiscalyear ORDER BY date_stop ASC LIMIT 1")
            first_fy = self.env.cr.dictfetchone()
            first_fy_date_start = datetime.strptime(
                first_fy['date_start'], '%Y-%m-%d')
            spread_start = invline.spread_date or \
                invline.invoice_id.date_invoice
            spread_date_start = datetime.strptime(spread_start, '%Y-%m-%d')
            fy_date_start = first_fy_date_start

            while spread_date_start < fy_date_start:
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

        spread_start_date = self._get_spread_start_date(
            invline, fy)
        spread_stop_date = self._get_spread_stop_date(
            invline, spread_start_date)

        while fy_date_start <= spread_stop_date:
            table.append({
                'fy_id': fy_id,
                'date_start': fy_date_start,
                'date_stop': fy_date_stop,
                'init': init_flag})
            fy_date_start = fy_date_stop + relativedelta(days=1)
            try:
                fy_id = fy_obj.find(fy_date_start)
                init_flag = False
            except:
                fy_id = False
            if fy_id:
                fy = fy_obj.browse(fy_id)
                if fy.state == 'done':
                    init_flag = True
                fy_date_stop = datetime.strptime(fy.date_stop, '%Y-%m-%d')
            else:
                fy_date_stop = fy_date_stop + relativedelta(years=1)

        digits = self.env['decimal.precision'].precision_get('Account')
        amount_to_spread = residual_amount = invline.price_subtotal

        # step 1:
        # calculate spread amount per fiscal year
        fy_residual_amount = residual_amount
        i_max = len(table) - 1
        invoice_sign = invline.price_subtotal >= 0 and 1 or -1
        for i, entry in enumerate(table):
            year_amount = self._compute_year_amount(invline)
            if invline.period_type == 'year':
                period_amount = year_amount
            elif invline.period_type == 'quarter':
                period_amount = year_amount/4
            elif invline.period_type == 'month':
                period_amount = year_amount/12
            if i == i_max:
                fy_amount = fy_residual_amount
            else:
                firstyear = i == 0 and True or False
                fy_factor = self._get_fy_duration_factor(
                    entry, invline, firstyear)
                fy_amount = year_amount * fy_factor
            if invoice_sign * (fy_amount - fy_residual_amount) > 0:
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

        # step 2: spread amount per fiscal year
        # over the periods
        fy_residual_amount = residual_amount
        line_date = False
        for i, entry in enumerate(table):
            period_amount = entry['period_amount']
            fy_amount = entry['fy_amount']
            period_duration = (
                invline.period_type == 'year' and 12) \
                or (invline.period_type == 'quarter' and 3) or 1
            if period_duration == 12:
                if invoice_sign * (fy_amount - fy_residual_amount) > 0:
                    fy_amount = fy_residual_amount
                lines = [{'date': entry['date_stop'], 'amount': fy_amount}]
                fy_residual_amount -= fy_amount
            elif period_duration in [1, 3]:
                lines = []
                fy_amount_check = 0.0
                if not line_date:
                    if period_duration == 3:
                        m = [x for x in [3, 6, 9, 12]
                             if x >= spread_start_date.month][0]
                        line_date = spread_start_date + \
                            relativedelta(month=m, day=31)
                    else:
                        line_date = spread_start_date + \
                            relativedelta(months=0, day=31)
                while line_date <= \
                        min(entry['date_stop'], spread_stop_date) and \
                        invoice_sign * (
                            fy_residual_amount - period_amount) > 0:
                    lines.append({'date': line_date, 'amount': period_amount})
                    fy_residual_amount -= period_amount
                    fy_amount_check += period_amount
                    line_date = line_date + \
                        relativedelta(months=period_duration, day=31)
                if i == i_max and \
                    (not lines or
                     spread_stop_date > lines[-1]['date']):
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
                raise Warning(
                    _('Programming Error!'),
                    _("Illegal value %s in invline.period_type.")
                    % invline.period_type)
            for line in lines:
                line['spreaded_value'] = amount_to_spread - residual_amount
                residual_amount -= line['amount']
                line['remaining_value'] = residual_amount
            entry['lines'] = lines

        return table

    @api.model
    def _get_spread_entry_name(self, line, seq):
        """ use this method to customise the name of the accounting entry """
        return (line.name or str(line.id)) + '/' + str(seq)

    def compute_spread_board(self):
        spread_obj = self.env['account.invoice.spread.line']
        digits = self.env['decimal.precision'].precision_get('Account')

        for invline in self:
            if invline.price_subtotal == 0.0:
                continue
            domain = [
                ('invoice_line_id', '=', invline.id),
                ('type', '=', 'spread'),
                '|', ('move_check', '=', True), ('init_entry', '=', True)]

            posted_spreads = spread_obj.search(domain,
                                               order='line_date desc'
                                               )
            last_spread_line = False
            if len(posted_spreads) > 0:
                last_spread_line = posted_spreads[0]

            domain = [
                ('invoice_line_id', '=', invline.id),
                ('type', '=', 'depreciate'),
                ('move_id', '=', False),
                ('init_entry', '=', False)]

            old_spreads = spread_obj.search(domain)
            if old_spreads:
                for spread in old_spreads:
                    spread.unlink()

            table = self._compute_spread_table(invline)
            if not table:
                continue

            # group lines prior to spread start period
            spread_start = invline.spread_date or \
                invline.invoice_id.date_invoice
            spread_start_date = datetime.strptime(
                spread_start, '%Y-%m-%d')
            lines = table[0]['lines']
            lines1 = []
            lines2 = []
            flag = lines[0]['date'] < spread_start_date
            for line in lines:
                if flag:
                    lines1.append(line)
                    if line['date'] >= spread_start_date:
                        flag = False
                else:
                    lines2.append(line)
            if lines1:
                def group_lines(x, y):
                    y.update({'amount': x['amount'] + y['amount']})
                    return y
                lines1 = [reduce(group_lines, lines1)]
                lines1[0]['spreaded_value'] = 0.0
            table[0]['lines'] = lines1 + lines2

            # check table with posted entries and
            # recompute in case of deviation
            if len(posted_spreads) > 0:
                last_spread_date = datetime.strptime(
                    last_spread_line.line_date, '%Y-%m-%d')
                last_date_in_table = table[-1]['lines'][-1]['date']
                if last_date_in_table <= last_spread_date:
                    raise Warning(
                        _('Error!'),
                        _("The duration of the spread conflicts with the "
                          "posted spread table entry dates."))

                for table_i, entry in enumerate(table):
                    residual_amount_table = \
                        entry['lines'][-1]['remaining_value']
                    if entry['date_start'] <= last_spread_date \
                            <= entry['date_stop']:
                        break
                if entry['date_stop'] == last_spread_date:
                    table_i += 1
                    line_i = 0
                else:
                    entry = table[table_i]
                    date_min = entry['date_start']
                    for line_i, line in enumerate(entry['lines']):
                        residual_amount_table = line['remaining_value']
                        if date_min <= last_spread_date <= line['date']:
                            break
                        date_min = line['date']
                    if line['date'] == last_spread_date:
                        line_i += 1
                table_i_start = table_i
                line_i_start = line_i

                # check if residual value corresponds with table
                # and adjust table when needed
                spreaded_value = 0.0
                for posted_spread in posted_spreads:
                    spreaded_value += posted_spread.amount

                residual_amount = invline.price_subtotal - spreaded_value
                amount_diff = round(
                    residual_amount_table - residual_amount, digits)
                if amount_diff:
                    entry = table[table_i_start]
                    fy_amount_check = 0.0
                    if entry['fy_id']:
                        fy_amount_check = 0.0
                        for posted_spread in posted_spreads:
                            line_date = posted_spread.line_date
                            if line_date >= entry['date_start']:
                                if line_date <= entry['date_stop']:
                                    fy_amount_check += posted_spread.amount

                    lines = entry['lines']
                    for line in lines[line_i_start:-1]:
                        line['spreaded_value'] = spreaded_value
                        spreaded_value += line['amount']
                        fy_amount_check += line['amount']
                        residual_amount -= line['amount']
                        line['remaining_value'] = residual_amount
                    lines[-1]['spreaded_value'] = spreaded_value
                    lines[-1]['amount'] = entry['fy_amount'] - fy_amount_check

            else:
                table_i_start = 0
                line_i_start = 0

            seq = len(posted_spreads)
            spread_line_id = last_spread_line and last_spread_line.id
            last_date = table[-1]['lines'][-1]['date']
            for entry in table[table_i_start:]:
                for line in entry['lines'][line_i_start:]:
                    seq += 1
                    name = self._get_spread_entry_name(invline, seq)
                    if line['date'] == last_date:
                        # ensure that the last entry of the table always
                        # depreciates the remaining value
                        existing_amount = 0.0
                        for existspread in spread_obj.search(
                            [('line_date', '<', last_date),
                             ('invoice_line_id', '=', invline.id)]):
                            existing_amount += existspread.amount

                        amount = invline.price_subtotal - existing_amount
                    else:
                        amount = line['amount']
                    previous_id = spread_line_id and spread_line_id.id or False
                    vals = {
                        'previous_id': previous_id,
                        'amount': amount,
                        'invoice_line_id': invline.id,
                        'name': name,
                        'line_date': line['date'].strftime('%Y-%m-%d'),
                        'init_entry': entry['init'],
                        }
                    spread_line_id = spread_obj.create(vals)
                line_i_start = 0

        return True
