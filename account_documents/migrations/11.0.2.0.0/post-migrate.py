# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.api import Environment, SUPERUSER_ID

import logging
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = Environment(cr, SUPERUSER_ID, {})
    model_id = env['ir.model'].search([('name', '=', 'account.invoice')])
    line = env['account.documents.type'].search([('model_id', '=', model_id.id)])
    if not line:
        line.create({'model_id': model_id.id, 'type': 'out_invoice', 'state': 'draft', 'print_name': 'Draft Invoice', 'name': 'Draft Invoice', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'out_invoice', 'state': 'open', 'print_name': 'Invoice - %s', 'name': 'Invoice', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'out_invoice', 'state': 'paid', 'print_name': 'Invoice - %s', 'name': 'Invoice'})
        line.create({'model_id': model_id.id, 'type': 'out_invoice', 'state': 'cancel', 'name': 'Cancelled Invoice', 'display': True})

        line.create({'model_id': model_id.id, 'type': 'out_refund', 'state': 'draft', 'print_name': 'Draft Credit Note', 'name': 'Draft Credit Note', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'out_refund', 'state': 'open', 'print_name': 'Credit Note - %s', 'name': 'Credit Note', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'out_refund', 'state': 'paid', 'print_name': 'Credit Note - %s', 'name': 'Credit Note'})
        line.create({'model_id': model_id.id, 'type': 'out_refund', 'state': 'cancel', 'name': 'Cancelled Credit Note', 'display': True})

        line.create({'model_id': model_id.id, 'type': 'in_invoice', 'state': 'draft', 'print_name': 'Vendor Bill', 'name': 'Draft Vendor Bill', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'in_invoice', 'state': 'open', 'print_name': 'Vendor Bill - %s', 'name': 'Vendor Bill', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'in_invoice', 'state': 'paid', 'print_name': 'Vendor Bill - %s', 'name': 'Vendor Bill'})
        line.create({'model_id': model_id.id, 'type': 'in_invoice', 'state': 'cancel', 'name': 'Cancelled Vendor Bill', 'display': True})

        line.create({'model_id': model_id.id, 'type': 'in_refund', 'state': 'draft', 'print_name': 'Draft Vendor Credit Note', 'name': 'Vendor Credit Note', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'in_refund', 'state': 'open', 'print_name': 'Vendor Credit Note - %s', 'name': 'Vendor Credit Note', 'display': True})
        line.create({'model_id': model_id.id, 'type': 'in_refund', 'state': 'paid', 'print_name': 'Vendor Credit Note - %s', 'name': 'Vendor Credit Note'})
        line.create({'model_id': model_id.id, 'type': 'in_refund', 'state': 'cancel', 'name': 'Cancelled Vendor Credit Note', 'display': True})
