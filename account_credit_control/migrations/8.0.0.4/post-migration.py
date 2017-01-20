# -*- encoding: utf-8 -*-
from openerp import api
from openerp import SUPERUSER_ID


def migrate(cr, version):
    with api.Environment.manage():
        env = api.Environment(cr, SUPERUSER_ID, {})
        env.cr.execute("""
            UPDATE credit_control_run SET company_id = (select company_id
            FROM credit_control_line where policy_id = credit_control_run.id
            limit 1)""")
