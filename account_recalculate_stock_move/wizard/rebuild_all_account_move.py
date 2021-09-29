# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import pytz
import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta

import logging
_logger = logging.getLogger(__name__)

_intervalTypes = {
    'days': lambda interval: relativedelta(days=interval),
    'hours': lambda interval: relativedelta(hours=interval),
    'weeks': lambda interval: relativedelta(days=7 * interval),
    'months': lambda interval: relativedelta(months=interval),
    'minutes': lambda interval: relativedelta(minutes=interval),
}


class WizardRebuildAllAccountMoves(models.TransientModel):
    _name = "wizard.rebuild.all.account.moves"

    rebuild_lines = fields.One2many('wizard.rebuild.lines.account.moves', 'rebuild_id', string='Rebuild lines')
    company_id = fields.Many2one(comodel_name='res.company', string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    interval_number = fields.Integer(default=1, help="Repeat every x.")
    interval_type = fields.Selection([('minutes', 'Minutes'),
                                      ('hours', 'Hours'),
                                      ('days', 'Days'),
                                      ('weeks', 'Weeks'),
                                      ('months', 'Months')], string='Interval Unit', default='days')
    nextcall = fields.Datetime(string='Next Execution Date', required=True, default=fields.Datetime.now,
                               help="Next planned execution date for this job.")
    user_id = fields.Many2one('res.users', string='Notified User', default=lambda self: self.env.user, required=True)
    check_product_moves = fields.Boolean('Product movement', default=True)
    check_invoice_moves = fields.Boolean('Invoice movement')

    def _rebuild_all_account_moves(self, begin_date, end_date):
        begin_date = begin_date.astimezone(pytz.UTC)
        end_date = end_date.astimezone(pytz.UTC)
        self.write({'rebuild_lines': self.env['wizard.rebuild.lines.account.moves']._get_lines(begin_date,
                                                                                               end_date,
                                                                                               self.company_id,
                                                                                               self.check_product_moves,
                                                                                               self.check_invoice_moves)})
        # _logger.info("LINE %s:%s->%s" % (begin_date, end_date, self.rebuild_lines))

    @api.multi
    def rebuild_all_account_moves(self):
        for record in self:
            end_date = fields.Datetime.from_string(record.nextcall)
            begin_date = end_date + _intervalTypes[record.interval_type](-record.interval_number)
            record._rebuild_all_account_moves(begin_date, end_date)
            # _logger.info("START %s:%s" % (begin_date, end_date))
            for line in record.rebuild_lines:
                _logger.info("LINE ACTION %s->%s" % (line.date, line.picking_id and line.picking_id.name or "none"))
                line._execute_rebuld()
                    # self.env['mail.thread'].message_post(
                    #     subject=_("Rebuild account move: (%s:%s:%s)") % (line.inventory_id.name, line.picking_id.name, line.landed_cost_id.name),
                    #     body=_(
                    #         "The inventory (%s), or picking (%s), or landed cost (%s) is rebuild.") % (
                    #              line.inventory_id.name,
                    #              line.picking_id.name,
                    #              line.landed_cost_id.name,
                    #          ),
                    #     partner_ids=[record.user_id.partner_id.id],
                    # )
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild_action(self):
        for record in self:
            action = self.env.ref('account_recalculate_stock_move.action_recalculate_all_account_move')
            action.with_context(self._context,
                                nextcall=record.nextcall,
                                interval_number=record.interval_number,
                                interval_type=record.interval_type).run()
            # _logger.info("ACTION %s" % action)
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def server_rebuild(self, nextcall=False, interval_number=1, interval_type='days'):
        # self.ensure_one()
        _logger.info("PARAMS %s-%s-%s" % (nextcall, interval_number, interval_type))
        if self._context.get('nextcall'):
            nextcall = self._context['nextcall']
        if self._context.get('interval_number'):
            interval_number = self._context['interval_number']
        if self._context.get('interval_type'):
            interval_type = self._context['interval_type']
        if not nextcall:
            nextcall = fields.Datetime.now()

        end_date = fields.Datetime.from_string(nextcall)
        begin_date = end_date + _intervalTypes[interval_type](-interval_number)
        if self._context.get('active_id'):
            record = self.browse(self._context['active_id'])
            record._rebuild_all_account_moves(begin_date, end_date)
        else:
            record = self.create({"company_id": self.env.user.company_id.id,
                            "interval_number": 1,
                            "interval_type": interval_type,
                            "nextcall": nextcall,
                            "user_id": self.env.user.id,
                            "check_product_moves": True,
                           })
            rebuild_lines = self.env['wizard.rebuild.lines.account.moves']._get_lines(begin_date,
                                                                                      end_date,
                                                                                      self.env.user.company_id,
                                                                                      record.check_product_moves,
                                                                                      record.check_invoice_moves,
                                                                                      rebuild_id=record.id)
            record.write({"rebuild_lines": rebuild_lines})
        # _logger.info("SERVER ACTION %s:%s:%s:%s:%s:%s:%s" % (self._context, begin_date, end_date, record.check_product_moves, self.env.user.company_id, record and record.rebuild_lines, rebuild_lines))

        # _logger.info("START %s:%s" % (begin_date, end_date))
        for line in record.rebuild_lines:
            _logger.info("LINE ACTION (%s:%s) %s->%s" % (begin_date, end_date, line.date, line.picking_id and line.picking_id.name or 'None'))
            line._execute_rebuld()

    @api.model
    def _transient_vacuum(self, force=False):
        cls = type(self)
        if not force and 'rebuild_lines' in cls._fields and cls.rebuild_lines.filtered(lambda r: not r.ready):
            cls._transient_check_count = 0
        return super(WizardRebuildAllAccountMoves, self)._transient_vacuum(force=force)


class WizardRebuildAllLinesAccountMoves(models.TransientModel):
    _name = "wizard.rebuild.lines.account.moves"
    _order = "date, sequence"

    rebuild_id = fields.Many2one('wizard.rebuild.all.account.moves', 'Wizard for rebuild', required=True,
                                 ondelete='cascade')
    picking_id = fields.Many2one('stock.picking', 'Stock Picking')
    landed_cost_id = fields.Many2one('stock.landed.cost', 'Landed Cost')
    inventory_id = fields.Many2one('stock.inventory', 'Stock Inventory')
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    date = fields.Datetime('Date')
    sequence = fields.Integer('Sequence')
    ready = fields.Boolean()
    check_product_moves = fields.Boolean('Product movement', related="rebuild_id.check_product_moves")
    check_invoice_moves = fields.Boolean('Invoice movement', related="rebuild_id.check_invoice_moves")

    def _get_lines(self, begin_date, end_date, company_id, check_product_moves, check_invoice_moves, rebuild_id=False):
        res = []
        begin_date = fields.Datetime.to_string(begin_date)
        end_date = fields.Datetime.to_string(end_date)
        # _logger.info("LINES %s:%s:%s:%s:%s:%s" % (begin_date, end_date, company_id, rebuild_id, check_product_moves, check_invoice_moves))
        if check_product_moves:
            # Inventory
            inventories = self.env['stock.inventory'].search([('date', '>=', begin_date),
                                                              ('date', '<=', end_date),
                                                              ('company_id', '=', company_id.id)])
            #_logger.info("INVENTORIES %s" % inventories)
            for inventory in inventories:
                res.append((0, 0, {
                    'date': inventory.date,
                    'inventory_id': inventory.id,
                    'sequence': 0,
                }))
                if rebuild_id:
                    res[-1][2]['rebuild_id'] = rebuild_id
            # Pickings
            pickings = self.env['stock.picking'].search([('date_done', '>=', begin_date),
                                                         ('date', '<=', end_date),
                                                         ('company_id', '=', company_id.id)])
            # _logger.info("PICKINGS %s" % pickings)
            for picking in pickings:
                res.append((0, 0, {
                    'date': picking.date,
                    'picking_id': picking.id,
                    'sequence': 3,
                }))
                if rebuild_id:
                    res[-1][2]['rebuild_id'] = rebuild_id

            # Landed cost
            landeds = self.env['stock.landed.cost'].search([('date', '>=', begin_date),
                                                            ('date', '<=', end_date),
                                                            ('company_id', '=', company_id.id)])
            # _logger.info("LANDED COST %s" % landeds)
            for landed in landeds:
                res.append((0, 0, {
                    'date': landed.date,
                    'landed_cost_id': landed.id,
                    'sequence': 4,
                }))
                if rebuild_id:
                    res[-1][2]['rebuild_id'] = rebuild_id

        if check_invoice_moves:
            # Invoices
            invoices = self.env['account.invoice'].search([('date', '>=', begin_date),
                                                           ('date', '<=', end_date),
                                                           ('company_id', '=', company_id.id),
                                                           ('', 'in', ['out_invoice', 'out_refund'])])
            #_logger.info("INVENTORIES %s" % inventories)
            for invoice in invoices:
                res.append((0, 0, {
                    'date': invoice.date,
                    'invoice_id': invoice.id,
                    'sequence': 5,
                }))
                if rebuild_id:
                    res[-1][2]['rebuild_id'] = rebuild_id

            invoices = self.env['account.invoice'].search([('date', '>=', begin_date),
                                                           ('date', '<=', end_date),
                                                           ('company_id', '=', company_id.id),
                                                           ('', 'in', ['in_invoice', 'in_refund'])])
            # _logger.info("INVENTORIES %s" % inventories)
            for invoice in invoices:
                res.append((0, 0, {
                    'date': invoice.date,
                    'invoice_id': invoice.id,
                    'sequence': 1,
                }))
                if rebuild_id:
                    res[-1][2]['rebuild_id'] = rebuild_id
        return res

    def _execute_rebuld(self):
        if self.inventory_id:
            self.inventory_id.with_context(self._context, rebuld_try=True).rebuild_account_move()
            self.write({'ready': True})

        if self.picking_id:
            self.picking_id.with_context(self._context, rebuld_try=True).rebuild_account_move()
            self.write({'ready': True})

        if self.landed_cost_id:
            self.landed_cost_id.with_context(self._context, rebuld_try=True).rebuild_account_move()
            self.write({'ready': True})
        return self.ready

    @api.model
    def _transient_vacuum(self, force=False):
        cls = type(self)
        if not force and 'ready' in cls._fields and cls.filtered(lambda r: not r.ready):
            cls._transient_check_count = 0
        return super(WizardRebuildAllLinesAccountMoves, self)._transient_vacuum(force=force)
