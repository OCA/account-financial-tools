# -*- encoding: utf-8 -*-
from openerp import models, fields, tools


class AccountReconcileTraceDirect(models.Model):
    _name = 'account.reconcile.trace.direct'
    _description = "Account Reconcile Trace Direct"
    _auto = False

    super_up_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Super Up Move',
        help='First account entry on reconciliation trace.')
    super_down_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Super Down Move',
        help='Last account entry on reconciliation trace.')
    up_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Up Move',
        help='Account entry on up reconciliation trace.')
    down_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Down Move',
        help='Account entry on down reconciliation trace.')
    up_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Up Journal',
        help='Journal on up reconciliation trace.')
    down_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Down Journal',
        help='Journal on down reconciliation trace.')
    up_amount = fields.Float(
        string='Up Amount',
        help='Amount on up reconciliation trace.')
    down_amount = fields.Float(
        string='Down Amount',
        help='Amount on down reconciliation trace.')
    up_date = fields.Date(
        string='Up Date',
        help='Date on up reconciliation trace.')
    down_date = fields.Date(
        string='Down Date',
        help='Date on down reconciliation trace.')
    up_ref = fields.Char(
        string='Up Ref',
        help='Reference of journal item on up reconciliation trace.')
    down_ref = fields.Char(
        string='Down Ref',
        help='Reference of journal item on down reconciliation trace.')
    up_name = fields.Char(
        string='Up Name',
        help='Name of journal item on up reconciliation trace.')
    down_name = fields.Char(
        string='Down Name',
        help='Name of journal item on down reconciliation trace.')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_reconcile_trace_direct')
        cr.execute("""
            create or replace view account_reconcile_trace_direct as (
                select  distinct up.id,
                        up.move_id as super_up_move_id,
                        down.move_id as super_down_move_id,
                        up.move_id as up_move_id,
                        down.move_id as down_move_id,
                        up.journal_id as up_journal_id,
                        down.journal_id as down_journal_id,
                        up.debit as up_amount,
                        down.credit as down_amount,
                        up.date as up_date,
                        down.date as down_date,
                        up.ref as up_ref,
                        down.ref as down_ref,
                        up.name as up_name,
                        down.name as down_name
                from    account_move_line up,
                        account_move_reconcile  rec,
                        account_move_line down
                where   up.debit > 0
                        and up.reconcile_id = rec.id
                        and down.credit > 0
                        and down.reconcile_id = rec.id
                order by up.move_id
        )""")


class AccountReconcileTraceRecursive(models.Model):
    _name = 'account.reconcile.trace.recursive'
    _description = "Account Reconcile Trace Recursive"
    _auto = False

    super_up_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Super Up Move',
        help='First account entry on reconciliation trace.')
    super_down_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Super Down Move',
        help='Last account entry on reconciliation trace.')
    up_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Up Move',
        help='Account entry on up reconciliation trace.')
    down_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Down Move',
        help='Account entry on down reconciliation trace.')
    up_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Up Journal',
        help='Journal on up reconciliation trace.')
    down_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Down Journal',
        help='Journal on down reconciliation trace.')
    up_amount = fields.Float(
        string='Up Amount',
        help='Amount on up reconciliation trace.')
    down_amount = fields.Float(
        string='Down Amount',
        help='Amount on down reconciliation trace.')
    up_date = fields.Date(
        string='Up Date',
        help='Date on up reconciliation trace.')
    down_date = fields.Date(
        string='Down Date',
        help='Date on down reconciliation trace.')
    up_ref = fields.Char(
        string='Up Ref',
        help='Reference of journal item on up reconciliation trace.')
    down_ref = fields.Char(
        string='Down Ref',
        help='Reference of journal item on down reconciliation trace.')
    up_name = fields.Char(
        string='Up Name',
        help='Name of journal item on up reconciliation trace.')
    down_name = fields.Char(
        string='Down Name',
        help='Name of journal item on down reconciliation trace.')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_reconcile_trace_recursive')
        cr.execute("""
            create or replace view account_reconcile_trace_recursive as (
                WITH RECURSIVE trace AS(
                    SELECT super_up_move_id,
                        super_down_move_id,
                        up_move_id,
                        down_move_id,
                        up_journal_id,
                        down_journal_id,
                        up_amount,
                        down_amount,
                        up_date,
                        down_date,
                        up_ref,
                        down_ref,
                        up_name,
                        down_name
                    FROM account_reconcile_trace_direct
                UNION
                    SELECT t.super_up_move_id,
                        rt.super_down_move_id,
                        rt.up_move_id,
                        rt.down_move_id,
                        t.up_journal_id,
                        rt.down_journal_id,
                        t.up_amount,
                        rt.down_amount,
                        t.up_date,
                        rt.down_date,
                        t.up_ref,
                        rt.down_ref,
                        t.up_name,
                        rt.down_name
                    FROM account_reconcile_trace_direct rt,
                        trace t
                    WHERE rt.up_move_id = t.down_move_id
                )
                SELECT row_number() OVER () as id,
                    super_up_move_id,
                    super_down_move_id,
                    up_move_id,
                    down_move_id,
                    up_journal_id,
                    down_journal_id,
                    up_amount,
                    down_amount,
                    up_date,
                    down_date,
                    up_ref,
                    down_ref,
                    up_name,
                    down_name
                FROM trace
        )""")
