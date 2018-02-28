# -*- coding: utf-8 -*-
# © <2018> PRISEHUB CIA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DateRange(models.Model):
    _inherit = 'date.range'

    accounting_state = fields.Selection(
        [
            ('open', 'Open'),
            ('close', 'Closed')
        ],
        string='State',
        required=True,
        readonly="1",
        default='open'
    )

    @api.multi
    def get_range(self, type_id, date):
        dmn = [
            ('type_id', '=', type_id),
            ('date_start', '<=', date),
            ('date_end', '>=', date)
        ]
        return self.search(dmn)

    @api.multi
    def closed(self):
        if self.accounting_state == 'close':
            return True
        return False

    @api.multi
    def action_change_state(self):
        self.ensure_one()
        if self.closed():
            self.accounting_state = 'open'
        else:
            self.accounting_state = 'close'


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.constrains('date')
    def _check_lock_date(self):
        for move in self:
            MSG = _('Not allow to post with date %s, period is closed.') % (move.date)  # noqa
            fy = self.env['date.range.type'].search([('fiscal_year', '=', True)])  # noqa
            acc_range = self.env['date.range'].get_range(fy.id, move.date)
            if acc_range.closed():
                raise ValidationError(MSG)
            return True
