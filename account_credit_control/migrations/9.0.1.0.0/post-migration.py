# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade
from openerp import fields


def migrate_followup_data(env):
    env.cr.execute(
        """SELECT aff.id, rc.name, aff.company_id
        FROM account_followup_followup aff, res_company rc
        WHERE aff.company_id = rc.id
        """
    )
    followup_count = env.cr.fetchall()
    for followup in followup_count:
        policy = env['credit.control.policy'].create({
            'name': followup[1],
            'company_id': followup[2],
        })
        env.cr.execute(
            """SELECT * FROM account_followup_followup_line
            WHERE followup_id = %s""",
            (followup[0], ),
        )
        lines = env.cr.dictfetchall()
        for line in lines:
            env['credit.control.policy.level'].create({
                'name': line['name'],
                'policy_id': policy.id,
                'level': line['sequence'],
                'computation_mode': 'net_days',
                'delay_days': line['delay'],
                'email_template_id': env.ref(
                    'account_credit_control.email_template_credit_control_base'
                ).id,
                'channel': 'email' if line['send_email'] else 'letter',
                'custom_text': line['description'],
                'custom_mail_text': line['description'],
            })


def set_followup_data(env):
    today = fields.Date.context_today(env.user)
    policy = env['credit.control.policy.level'].search([])[:-1]
    if policy:
        env.cr.execute("""
            SELECT aml.* FROM account_move_line aml, account_account aa
            WHERE aml.account_id = aa.id
            AND invoice_id IS NOT NULL
            AND aa.internal_type = 'receivable'
            AND aml.reconciled IS NULL
            AND aml.date_maturity < %s
        """, (today,))
        data = env.cr.dictfetchall()
        for line in data:
            env['credit.control.line'].create({
                'date': today,
                'date_due': line['date_maturity'],
                'state': 'draft',
                'channel': 'letter',
                'invoice_id': line['invoice_id'],
                'partner_id': line['partner_id'],
                'amount_due': line['debit'],
                'balance_due': line['debit'],
                'move_line_id': line['id'],
                'account_id': line['account_id'],
                'policy_level_id': policy.id,
            })


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if openupgrade.table_exists(env.cr, 'account_followup_followup'):
        migrate_followup_data(env)
        set_followup_data(env)
