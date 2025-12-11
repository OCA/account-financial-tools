# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class WizardUpdateChartsAccounts(models.TransientModel):
    _inherit = "wizard.update.charts.accounts"

    code_digits = fields.Integer()

    @api.onchange("chart_template")
    def _onchage_chart_template(self):
        res = super()._onchage_chart_template()
        self.code_digits = self.company_id.account_code_digits or self.code_digits
        return res

    def _update_accounts(self, t_data):
        res = super()._update_accounts(t_data)
        self.company_id.account_code_digits = self.code_digits
        return res

    @api.model
    def diff_fields(self, record_values, real):
        res = super().diff_fields(record_values, real)
        if real._name != "account.account" or "code" not in record_values:
            return res
        ignore = self.fields_to_ignore(real._name)
        if "code" in ignore:
            return res
        record_values["code"] = self.padded_code(record_values["code"])
        if record_values["code"] != real["code"]:
            res["code"] = record_values["code"]
        return res

    def _update_accounts(self, t_data):
        res = super()._update_accounts(t_data)
        self.company_id.account_code_digits = self.code_digits

        failed_accounts = (
            self.env["account.account"]
            .search([("company_ids", "in", self.company_id.id)])
            .filtered(lambda a: len(a.code) != self.code_digits)
        )
        if failed_accounts:
            account_names = ", ".join(failed_accounts.mapped("display_name"))
            msg = _(
                "The following accounts could not be automatically updated to "
                "%(digits)s digits because they are not created by the chart "
                "of accounts template. Please update them manually: %(accounts)s",
                digits=self.code_digits,
                accounts=account_names,
            )
            _logger.info(msg)
            self.log = f"{msg}\n{self.log}" if self.log else msg
        return res
