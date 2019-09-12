# -*- coding: utf-8 -*-
# Copyright 2019 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import logging
from datetime import date, timedelta
from odoo import _, api, exceptions, fields, models, tools


_logger = logging.getLogger(__name__)


class AccountFindBalanceInconsistency(models.TransientModel):
    _name = 'account.find.balance.inconsistency'
    _inherit = 'accounting.report'
    _description = 'Find balance inconsistencies'

    find_date_from = fields.Date(
        required=True, default=lambda self: fields.Date.to_string(
            date(date.today().year, 1, 1),
        ),
    )
    find_date_to = fields.Date(
        required=True, default=lambda self: fields.Date.to_string(
            date(date.today().year, 12, 31),
        ),
    )
    account_report_id = fields.Many2one(
        string='1st report', default=lambda self: self.env.ref(
            'account.account_financial_report_assets0', False,
        ),
    )
    account_report2_id = fields.Many2one(
        'account.financial.report', string='2nd report', required=True,
        default=lambda self: self.env.ref(
            'account.account_financial_report_liabilitysum0', False,
        ),
    )

    @api.multi
    def check_report(self):
        self.ensure_one()
        date = fields.Date.from_string(self.find_date_from)
        date_end = fields.Date.from_string(self.find_date_to)
        reports = self.account_report_id + self.account_report2_id
        report_model = self.env['report.account.report_financial']
        while date <= date_end:
            _logger.debug('Working on date %s', date)
            self.write({
                'date_from': False,
                'date_to': fields.Date.to_string(date),
            })
            data = super(AccountFindBalanceInconsistency, self).check_report()
            used_context = data['data']['form']['used_context']
            balances = report_model.with_context(
                used_context,
            )._compute_report_balance(reports)
            balance1 = balances[self.account_report_id.id]['balance']
            balance2 = balances[self.account_report2_id.id]['balance']
            if tools.float_compare(
                    abs(balance1), abs(balance2), precision_digits=2,
            ) != 0:
                domain = [
                    ('move_id.state', '=', used_context['state']),
                    ('move_id.journal_id', 'in', used_context['journal_ids']),
                    ('date', '=', fields.Date.to_string(date)),
                ]
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Journal items on first day of inconsistency'),
                    'res_model': 'account.move.line',
                    'views': [(False, 'tree'), (False, 'form')],
                    'domain': domain,
                }
            date += timedelta(days=1)
        raise exceptions.UserError(_(
            'No inconsistencies found for selected reports and interval'
        ))
