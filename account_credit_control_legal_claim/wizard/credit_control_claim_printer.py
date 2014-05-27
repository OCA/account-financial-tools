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
import base64
import netsvc
from openerp.osv import orm, fields


class credit_control_legal_printer(orm.TransientModel):
    """Print claim requisition letter

    And manage related credit lines

    """

    def _filter_claim_invoices(self, cr, uid, invoices, context=None):
        """ Return invoices that are related to a claim
        concretly that means the invoice must be related
        to active credit line related to a claim policy level

        :param invoices: list on invoices record to be filtered

        """

        filtered = []
        for inv in invoices:
            if any(x for x in inv.credit_control_line_ids
                   if x.policy_level_id.is_legal_claim):
                filtered.append(inv)
        return filtered

    def _get_invoice_ids(self, cr, uid, context=None):
        """Return invoices ids to be treated form context
        A candidate invoice is related to a claim

        """
        inv_model = self.pool['account.invoice']
        if context is None:
            context = {}
        res = False
        if context.get('active_model') != 'account.invoice':
            return res
        res = context.get('active_ids', False)
        if res:
            invoices = inv_model.browse(cr, uid, res, context=context)
            filtered = self._filter_claim_invoices(cr, uid, invoices,
                                                   context=context)
            res = [x.id for x in filtered]
        return res

    _name = "credit.control.legal.claim.printer"
    _rec_name = 'id'
    _columns = {
        'mark_as_claimed': fields.boolean('Mark as Claimed'),
        'report_file': fields.binary('Report File',
                                     readonly=True),
        'report_name': fields.char('Report Name'),
        'invoice_ids': fields.many2many('account.invoice',
                                        string='Invoices'),
        'state': fields.selection([('draft', 'Draft'),
                                   ('done', 'Done')]),
    }

    _defaults = {
        'invoice_ids': _get_invoice_ids,
        'mark_as_claimed': True,
    }

    def _generate_report(self, cr, uid, invoice_ids, context=None):
        """Generate claim requisition report.

        :param invoice_ids: list of invoice ids to print

        :returns: report file

        """
        service = netsvc.LocalService('report.credit_control_legal_claim_requisition')
        result, format = service.create(cr, uid, invoice_ids, {}, {})
        return result

    def _mark_invoice_as_claimed(self, cr, uid, invoice, context=None):
        """Mark related credit line of an invoice as overridden.

        Only non claim credit line will be marked

        :param invoice: invoice recorrd to treat

        :returns: marked credit lines
        """
        lines  = [x for x in invoice.credit_control_line_ids
                    if not x.policy_level_id.is_legal_claim]
        credit_line_model = self.pool['credit.control.line']
        data = {'manually_overridden': True}
        credit_line_model.write(cr, uid,
                                [x.id for x in lines],
                                data,
                                context=context)
        return lines

    def print_claims(self, cr, uid, wiz_id, context=None):
        """Generate claim requisition report and manage credit lines.

        Non claim credit lines will be overridden

        :param invoice_ids: list of invoice ids to print

        :returns: an ir.action  to himself

        """
        if isinstance(wiz_id, list):
            assert len(wiz_id) == 1
            wiz_id = wiz_id[0]

        current = self.browse(cr, uid, wiz_id, context=context)
        invs = self._filter_claim_invoices(cr, uid, current.invoice_ids,
                                           context=context)
        invoice_ids = [x.id for x in invs]
        assert invoice_ids
        report_file = self._generate_report(cr, uid, invoice_ids,
                                            context=context)
        current.write(
            {'report_file': base64.b64encode(report_file),
             'report_name': 'claim_letters_%s.pdf' % fields.datetime.now(),
             'state': 'done'}
        )
        if current.mark_as_claimed:
            for inv in invs:
                self._mark_invoice_as_claimed(cr, uid, inv, context=context)

        return {'type': 'ir.actions.act_window',
                'res_model': 'credit.control.legal.claim.printer',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': current.id,
                'views': [(False, 'form')],
                'target': 'new',
                }
