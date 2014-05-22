 # -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
##############################################################################
import time
import operator
from itertools import groupby
from itertools import chain
from openerp.report import report_sxw
from openerp.osv import fields

class CreditClaimRequisition(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(CreditClaimRequisition, self).__init__(cr, uid, name,
                                                     context=context)
        self.localcontext.update({
            'time': time,
            'cr': cr,
            'uid': uid,
            'today': fields.date.today(),
            'compute_dunning_fees': self.compute_dunning_fees,
            'compute_due_amount': self.compute_due_amount,
            'get_legal_claim_fees': self.get_legal_claim_fees,
            'compute_paid_amount': self.compute_paid_amount,
        })

    def _active_line(self, cr, uid, line, context=None):
        return (line.state not in ('draft', 'ignored') and
                not line.manually_overriden)

    def compute_dunning_fees(self, invoices):
        lines = chain.from_iterable([x.credit_control_line_ids for x in invoices])
        return sum(x.dunning_fees_amount for x in lines
                   if self._active_line(self.cr, self. uid, x))

    def get_legal_claim_fees(self, part, invoices):
        scheme = part.claim_office_id.fees_scheme_id
        return scheme.get_fees_from_invoices([x.id for x in invoices])

    def compute_due_amount(self, invoices):
        return sum(x.residual for x in invoices)

    def compute_paid_amount(self, invoices):
        return sum(x.amount_total - x.residual for x in invoices)

    def set_context(self, objects, data, ids, report_type=None):
        """Group invoice by partner and currency and replace objects
        with partner

        """
        new_objects = []
        for key, invoices in groupby(objects, lambda x: (x.partner_id, x.currency_id)):
            part = key[0]
            part.claim_invoices = list(invoices)
            part.claim_currency = key[1]
            new_objects.append(part)
        return super(CreditClaimRequisition, self).set_context(
            new_objects, data, id, report_type=report_type
        )

report_sxw.report_sxw('report.credit_control_legal_claim_requisition',
                      'credit.control.communication',
                      'addons/account_credit_control_legal_claim/report/credit_control_legal_claim.html.mako',
                      parser=CreditClaimRequisition)
