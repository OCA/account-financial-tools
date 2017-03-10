# -*- coding: utf-8 -*-
# Copyright 2004-2010 Tiny SPRL (<http://tiny.be>)
# Copyright 2007 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models
from openerp import tools


class AccountFollowupStat(models.Model):
    _name = "account_followup.stat"
    _description = "Follow-up Statistics"
    _rec_name = 'partner_id'
    _auto = False

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        readonly=True,
    )
    date_move = fields.Date(
        string='First move',
        readonly=True,
    )
    date_move_last = fields.Date(
        string='Last move',
        readonly=True,
    )
    date_followup = fields.Date(
        string='Latest followup',
        readonly=True,
    )
    followup_id = fields.Many2one(
        comodel_name='account_followup.followup.line',
        string='Follow Ups',
        readonly=True,
        ondelete="cascade",
    )
    balance = fields.Float(
        readonly=True,
    )
    debit = fields.Float(
        readonly=True,
    )
    credit = fields.Float(
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    blocked = fields.Boolean(
        readonly=True,
    )
    _order = 'date_move'

    def _select(self):
        select_str = """
            SELECT l.id as id,
                l.partner_id AS partner_id,
                min(l.date) AS date_move,
                max(l.date) AS date_move_last,
                max(l.followup_date) AS date_followup,
                max(l.followup_line_id) AS followup_id,
                sum(l.debit) AS debit,
                sum(l.credit) AS credit,
                sum(l.balance) AS balance,
                l.company_id AS company_id,
                l.blocked as blocked
        """
        return select_str

    def _from(self):
        from_str = """
            account_move_line l
                LEFT JOIN account_account a ON (l.account_id = a.id)
        """
        return from_str

    def _where(self):
        where_str = """
            WHERE l.reconciled is FALSE
                AND l.partner_id IS NOT NULL
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY l.id, l.partner_id, l.company_id, l.blocked
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            create or replace view %s as (
                %s
                FROM
                    %s
                %s
                %s
            )""" % (self._table, self._select(), self._from(), self._where(),
                    self._group_by(),))


class AccountFollowupStatByPartner(models.Model):
    _name = "account_followup.stat.by.partner"
    _description = "Follow-up Statistics by Partner"
    _rec_name = 'partner_id'
    _auto = False

    @api.model
    def _get_invoice_partner_id(self):
        for rec in self:
            rec.invoice_partner_id = rec.partner_id.address_get(
                adr_pref=['invoice']
            ).get('invoice', rec.partner_id)

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        readonly=True,
    )
    date_move = fields.Date(
        string='First move',
        readonly=True,
    )
    date_move_last = fields.Date(
        string='Last move',
        readonly=True,
    )
    date_followup = fields.Date(
        string='Latest follow-up',
        readonly=True,
    )
    max_followup_id = fields.Many2one(
        comodel_name='account_followup.followup.line',
        string='Max Follow Up Level',
        readonly=True,
        ondelete="cascade",
    )
    balance = fields.Float(
        string='Balance',
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        readonly=True,
    )
    invoice_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Invoice Address',
        compute=_get_invoice_partner_id,
    )

    _depends = {
        'account.move.line': [
            'account_id', 'company_id', 'credit', 'date', 'debit',
            'followup_date', 'followup_line_id', 'partner_id', 'reconciled',
        ],
        'account.account': ['internal_type'],
    }

    def _select(self):
        select_str = """
            SELECT l.partner_id * 10000::bigint + l.company_id as id,
                l.partner_id AS partner_id,
                min(l.date) AS date_move,
                max(l.date) AS date_move_last,
                max(l.followup_date) AS date_followup,
                max(l.followup_line_id) AS max_followup_id,
                sum(l.balance) AS balance,
                l.company_id as company_id
        """
        return select_str

    def _from(self):
        from_str = """
            account_move_line l
                LEFT JOIN account_account a ON (l.account_id = a.id)
        """
        return from_str

    def _where(self):
        where_str = """
            WHERE
                a.internal_type = 'receivable'
                AND l.reconciled is FALSE
                AND l.partner_id IS NOT NULL
                GROUP BY l.partner_id, l.company_id
        """
        return where_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        # Here we don't have other choice but to create a virtual ID based
        # on the concatenation of the partner_id and the company_id, because
        # if a partner is shared between 2 companies, we want to see 2 lines
        # for him in this table. It means that both company should be able
        # to send him follow-ups separately . An assumption that the number of
        # companies will not reach 10 000 records is made, what should be
        # enough for a time.
        self._cr.execute("""
            create view %s as (
                %s
                FROM %s
                %s
            )""" % (self._table, self._select(), self._from(), self._where(),))
