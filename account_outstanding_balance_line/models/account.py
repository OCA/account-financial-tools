# -*- coding: utf-8 -*-
# Copyright 2018 PlanetaTIC - Lluís Rovira <lrovira@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.multi
    def _compute_outstanding_balance(self):
        cr = self.env.cr
        sql = ("""SELECT l.account_id\
            FROM account_move_line l\
            WHERE l.id IN %s\
            GROUP BY l.account_id""")
        params = (tuple(self.ids),)
        cr.execute(sql, params)
        res = cr.fetchall()
        if len(res) > 1:
            for acc_move_line in self:
                acc_move_line.outstanding_balance = 0
        else:
            where_partner = ''
            group_by_partner = ''
            receivable_acc = self.env['res.partner'].search(
                    [('property_account_receivable_id', '=', res[0][0])])
            payable_acc = self.env['res.partner'].search(
                    [('property_account_payable_id', '=', res[0][0])])
            if receivable_acc or payable_acc:
                group_by_partner = ', l.partner_id'
            sql = ("""SELECT l.account_id\
                FROM account_move_line l\
                WHERE l.id IN %s\
                GROUP BY l.account_id""") + group_by_partner
            params = (tuple(self.ids),)
            cr.execute(sql, params)
            res = cr.fetchall()
            if len(res) > 1:
                for acc_move_line in self:
                    acc_move_line.outstanding_balance = 0
            else:
                for acc_move_line in self:
                    if receivable_acc or payable_acc:
                        where_partner = (' AND l.partner_id = %s') % \
                            acc_move_line.partner_id.id
                    sql = ("""SELECT COALESCE(SUM(l.debit),0) -\
                        COALESCE(SUM(l.credit), 0) AS balance\
                        FROM account_move_line l\
                        WHERE l.account_id = %s AND\
                        l.date <= %s AND l.id <= %s""") + where_partner + \
                        ("""GROUP BY l.account_id""") + group_by_partner
                    params = (acc_move_line.account_id.id, acc_move_line.date,
                              acc_move_line.id)
                    cr.execute(sql, params)
                    bal = cr.fetchone()
                    acc_move_line.outstanding_balance = bal[0]

    outstanding_balance = fields.Monetary(string='Outstanding balance',
        currency_field='company_currency_id',
        compute='_compute_outstanding_balance')
