# Copyright 2009-2019 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class WizAccountAssetReport(models.TransientModel):
    _name = "wiz.account.asset.report"
    _description = "Financial Assets report"

    asset_group_id = fields.Many2one(
        comodel_name="account.asset.group",
        string="Asset Group",
        default=lambda self: self._default_asset_group_id(),
    )
    date_from = fields.Date(
        string="Start Date",
        required=True,
        default=lambda self: self._default_fy_dates()["date_from"],
    )
    date_to = fields.Date(
        string="End Date",
        required=True,
        default=lambda self: self._default_fy_dates()["date_to"],
    )
    draft = fields.Boolean(string="Include draft assets")
    company_ids = fields.Many2many(
        comodel_name="res.company",
        string="Companies",
        domain=lambda self: [("id", "in", self.env.user.company_ids.ids)],
    )

    @api.model
    def _default_asset_group_id(self):
        return (
            self.env["account.asset.group"]
            .search([("parent_id", "=", False)], limit=1)
            .id
        )

    @api.model
    def _default_fy_dates(self):
        fy_dates = self.env.company.compute_fiscalyear_dates(fields.date.today())
        return fy_dates

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for wiz in self:
            if wiz.date_to <= wiz.date_from:
                raise UserError(_("The Start Date must precede the Ending Date."))

    def xls_export(self):
        self.ensure_one()
        report_name = "account_asset_management.asset_report_xls"
        if self.asset_group_id:
            prefix = (
                unicodedata.normalize("NFKD", self.asset_group_id.name)
                .encode("ascii", "ignore")
                .decode("ascii")
            )
            prefix = "".join(x for x in prefix if x.isalnum())
            report_file = "{}_asset_report".format(prefix)
        else:
            report_file = "asset_report"
        report = {
            "type": "ir.actions.report",
            "report_type": "xlsx",
            "report_name": report_name,
            "context": dict(self.env.context, report_file=report_file),
            "data": {"dynamic_report": True},
        }
        return report
