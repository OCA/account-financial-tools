# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rule_name = "account_spread_cost_revenue.account_spread_multi_company_rule"
    rule = env.ref(rule_name, raise_if_not_found=False)
    if rule:
        domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
        rule.write({"domain_force": domain})

    rule_name = "account_spread_cost_revenue.account_spread_template_multi_company_rule"
    rule = env.ref(rule_name, raise_if_not_found=False)
    if rule:
        domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
        rule.write({"domain_force": domain})

    rule_name = (
        "account_spread_cost_revenue.account_spread_template_auto_multi_company_rule"
    )
    rule = env.ref(rule_name, raise_if_not_found=False)
    if rule:
        domain = "['|',('company_id','=',False),('company_id','in',company_ids)]"
        rule.write({"domain_force": domain})
