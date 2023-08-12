# Copyright 2022-2023 Moduon Team S.L. <info@moduon.team>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def execute_update_check_vies(self):
        # Only parent partners, children are synced from parent
        count_partners = self.env["res.partner"].search_count(
            [("parent_id", "=", False)]
        )
        self.env["res.partner"].search([("parent_id", "=", False)]).check_vat()
        return {
            "effect": {
                "fadeout": "slow",
                "message": _("Vies passed calculated in %s partners") % count_partners,
                "img_url": "/web/static/src/img/smile.svg",
                "type": "rainbow_man",
            }
        }
