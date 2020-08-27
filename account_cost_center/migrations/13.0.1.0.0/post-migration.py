# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rule = env.ref(
        "account_cost_center.account_cost_center_comp_rule", raise_if_not_found=False,
    )
    if rule:
        domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
        rule.write({"domain_force": domain})
