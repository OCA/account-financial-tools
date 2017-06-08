# -*- coding: utf-8 -*-
# © 2012, Joel Grand-Guillaume, Camptocamp SA.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api, exceptions, _


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.constrains('journal_id', 'period_id', 'date')
    def _check_fiscal_year(self):
        for move in self:
            if move.journal_id.allow_date_fy:
                date_start = move.period_id.fiscalyear_id.date_start
                date_stop = move.period_id.fiscalyear_id.date_stop
                if not date_start <= move.date <= date_stop:
                    raise exceptions.Warning(
                        _('You cannot create entries with date not in the '
                          'fiscal year of the chosen period'))
        return True
