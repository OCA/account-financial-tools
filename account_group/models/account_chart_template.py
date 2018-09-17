# coding: utf-8
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountChartTemplate(models.Model):
    _inherit = "account.chart.template"

    def _get_account_vals(self, company, account_template, code_acc,
                          tax_template_ref):
        """Add account group to created accounts."""
        res = super(AccountChartTemplate, self)._get_account_vals(
            company, account_template, code_acc, tax_template_ref,
        )
        res['group_id'] = account_template.group_id.id
        return res
