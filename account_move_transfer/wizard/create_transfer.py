# -*- coding: utf-8 -*-
# Copyright 2015-2017 See manifest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
import time


class WizardCreateMoveTransfer(models.TransientModel):
    _name = "wizard.create.move.transfer"

    account_move_id = fields.Many2one(comodel_name="account.move", string="Account move")
    account_move_line_ids = fields.One2many(comodel_name="wizard.create.move.line.transfer", inverse_name="account_move_id")
    partner_id = fields.Many2one('res.partner', 'Partner')
    journal_id = fields.Many2one('account.journal', string='Journal')
    date = fields.Date(required=True, default=fields.Date.context_today)

    move_line_type = fields.Selection(
        [('cr', 'Credit'), ('dr', 'Debit')], required=True, default='dr')
    account_id = fields.Many2one('account.account', string="Contra Account", required=True)

    @api.onchange('move_line_type', 'account_id')
    def onchange_move_line_type(self):
        if self.account_id:
            self.account_move_line_ids = False
            amount = 0.0
            move_line_vals = []
            for line in self.account_move_id.line_ids.filtered(lambda r: (r.credit != 0.0 and self.move_line_type == "cr") or (r.debit != 0.0 and self.move_line_type == 'dr')):
                amount += line.debit + line.credit
                self.account_move_line_ids.new({
                            'account_move_id': self.id,
                            'account_id': line.account_id and line.account_id.id,
                            'name': line.name,
                            'quantity': line.quantity,
                            'product_uom_id': line.product_uom_id and line.product_uom_id.id,
                            'product_id': line.product_id and line.product_id.id,
                            'debit': line.credit,
                            'credit': line.debit,
                            'analytic_account_id': line.analytic_account_id,
                            'analytic_tag_ids': [(6, False, line.analytic_tag_ids.ids)],
                            'company_id': line.company_id.id,
                            'currency_id': line.currency_id.id,
                            'date': self.date,
                            })
            self.account_move_line_ids.new({
                'account_move_id': self.id,
                'account_id': self.account_id and self.account_id.id,
                'debit': self.move_line_type == "dr" and amount or 0.0,
                'credit': self.move_line_type == "cr" and amount or 0.0,
                'date': self.date,
            })
            for line in self.account_move_line_ids:
                move_line_val = line._convert_to_write(line._cache)
                move_line_vals.append((0, False, move_line_val))
            self.account_move_line_ids = move_line_vals
            #self.write({"account_move_line_ids": []})

    @api.multi
    def load_template(self):
        self.ensure_one()
        name = self.account_move_id.name
        partner = self.partner_id.id
        moves = self.env['account.move']
        for journal in self.journal_id:
            lines = []
            move = self._create_move(name, journal.id, partner, self.account_move_id.id)
            for line in self.account_move_line_ids:
                lines.append((0, 0, self._prepare_line(line, partner, move)))
            move.write({'line_ids': lines})
        return {
            'domain': [('id', 'in', [move.id])],
            'name': 'Entries from transfer: %s' % name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    @api.model
    def _create_move(self, ref, journal_id, partner_id, account_move_id):
        return self.env['account.move'].create({
            'ref': ref,
            'journal_id': journal_id,
            'partner_id': partner_id,
            'origin_move_id': account_move_id,
        })

    @api.model
    def _prepare_line(self, line, partner_id, move):
        values = {
            'name': line.name,
            'move_id': move.id,
            'analytic_account_id': line.analytic_account_id.id,
            'analytic_tag_ids': line.analytic_tag_ids,
            'account_id': line.account_id.id,
            'company_id': line.company_id.id,
            'date': time.strftime('%Y-%m-%d'),
            'credit': line.credit,
            'debit': line.debit,
            'partner_id': partner_id,
        }
        return values


class WizardCreateMoveLineTransfer(models.TransientModel):
    _description = 'Transfers Lines'
    _name = "wizard.create.move.line.transfer"

    @api.model
    def _get_currency(self):
        currency = False
        context = self._context or {}
        if context.get('default_journal_id', False):
            currency = self.env['account.journal'].browse(context['default_journal_id']).currency_id
        return currency

    account_move_id = fields.Many2one(comodel_name="wizard.create.move.transfer", string="Account move")
    account_id = fields.Many2one('account.account', required=True)
    name = fields.Char(string="Label")
    quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
        help="The optional quantity expressed by this line, eg: number of product sold. The quantity is not a legal requirement but is very useful for some reports.")
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure')
    product_id = fields.Many2one('product.product', string='Product')
    debit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(default=0.0, currency_field='company_currency_id')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic tags')
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=_get_currency,
        help="The optional other currency if it is a multi-currency entry.")
    date = fields.Date(related='account_move_id.date', string='Date', index=True, store=True, copy=False)  # related is required
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True,
        help='Utility field to express amount currency', store=True)
    journal_id = fields.Many2one('account.journal', related='account_move_id.journal_id', string='Journal', store=True, copy=False)  # related is required