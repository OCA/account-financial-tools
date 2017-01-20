# -*- encoding: utf-8 -*-
from openerp import api
from openerp import SUPERUSER_ID


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        env.cr.execute("""
            UPDATE credit_control_run SET company_id = (SELECT ccp.company_id
            FROM credit_run_policy_rel AS crpr JOIN credit_control_policy AS ccp
            ON (crpr.policy_id = ccp.id) WHERE crpr.run_id = credit_control_run.id
            LIMIT 1)""")
