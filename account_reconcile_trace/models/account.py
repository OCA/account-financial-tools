# -*- encoding: utf-8 -*-
from openerp import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    trace_down_ids = fields.One2many(
        comodel_name='account.reconcile.trace.recursive',
        inverse_name='super_up_move_id',
        string='Trace Down')
    trace_up_ids = fields.One2many(
        comodel_name='account.reconcile.trace.recursive',
        inverse_name='super_down_move_id',
        string='Trace Up')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    trace_down_ids = fields.One2many(
        'account.reconcile.trace.recursive',
        related='move_id.trace_down_ids',
        string='Trace Down')
    trace_up_ids = fields.One2many(
        'account.reconcile.trace.recursive',
        related='move_id.trace_up_ids',
        string='Trace Up')
