# -*- coding: utf-8 -*-
#
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#    All Rights Reserved
#
#    WARNING: This program as such is intended to be used by professional
#    programmers who take the whole responsibility of assessing all potential
#    consequences resulting from its eventual inadequacies and bugs.
#    End users who are looking for a ready-to-use solution with commercial
#    guarantees and support are strongly advised to contact a Free Software
#    Service Company.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#

from openerp import models, api, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
from openerp import exceptions


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def action_move_create(self):
        res = super(account_invoice, self).action_move_create()
        for inv in self:
            if inv.journal_id.check_chronology:
                invoices = \
                    self.search([('state', 'not in',
                                  ['open', 'paid', 'cancel', 'proforma',
                                   'proforma2']),
                                 ('date_invoice', '!=', False),
                                 ('date_invoice', '<', inv.date_invoice),
                                 ('journal_id', '=', inv.journal_id.id)],
                                limit=1)
                if len(invoices) > 0:
                    date_invoice_format = datetime\
                        .strptime(inv.date_invoice,
                                  DEFAULT_SERVER_DATE_FORMAT)
                    date_invoice_tz = fields\
                        .Date.context_today(self, date_invoice_format)
                    raise exceptions.Warning(_("Chronology Error."
                                               " Please confirm older draft"
                                               " invoices before %s and"
                                               " try again.") %
                                             date_invoice_tz)

                if inv.internal_number is False:
                    invoices = self.search([('state', 'in', ['open', 'paid']),
                                            ('date_invoice', '>',
                                             inv.date_invoice),
                                            ('journal_id', '=',
                                             inv.journal_id.id)],
                                           limit=1)
                    if len(invoices) > 0:
                        date_invoice_format = datetime\
                            .strptime(inv.date_invoice,
                                      DEFAULT_SERVER_DATE_FORMAT)
                        date_invoice_tz = fields\
                            .Date.context_today(self, date_invoice_format)
                        raise exceptions.Warning(_("Chronology Error. There"
                                                   " exist at least one"
                                                   " invoice with a date"
                                                   " posterior to %s.") %
                                                 date_invoice_tz)
        return res
