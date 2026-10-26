# Copyright 2022 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class WizardUpdateChartsAccounts(models.TransientModel):
    _inherit = "wizard.update.charts.accounts"

    def _domain_taxes_to_deactivate(self, found_taxes_ids):
        domain = super()._domain_taxes_to_deactivate(found_taxes_ids)
        domain.append(("oss_country_id", "=", False))
        return domain
