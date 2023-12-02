# Copyright 2023 Engenere - Antônio S. P. Neto
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    update_account_spread_invoice_relation(env.cr)
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


def update_account_spread_invoice_relation(cr):
    openupgrade.logged_query(
        cr,
        """
        UPDATE account_spread accs
        SET invoice_line_id = aml.id
        FROM account_move_line aml
        WHERE accs.{old_inv_line_id} = aml.old_invoice_line_id
        """.format(
            old_inv_line_id=openupgrade.get_legacy_name("invoice_line_id")
        ),
    )
