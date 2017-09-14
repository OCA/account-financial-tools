# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not openupgrade.table_exists(env.cr, 'account_followup_followup'):
        # This is not coming from account_followup migration
        return
    # Remove no update rules that no longer applies
    env.ref('account_credit_control.account_followup_comp_rule').unlink()
    env.ref(
        'account_credit_control.account_followup_stat_by_partner_comp_rule'
    ).unlink()
