# Copyright 2013-2020 Akretion France (https://akretion.com/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.onchange("property_account_position_id")
    def fiscal_position_change(self):
        """Warning if the fiscal position requires a VAT number and the
        partner doesn't have one yet"""
        fp = self.property_account_position_id
        if fp.vat_required and not self.vat:
            return {
                "warning": {
                    "title": _("Missing VAT number:"),
                    "message": _(
                        "You have set the fiscal position '%s' "
                        "that require customers to have a VAT number. "
                        "If you plan to use this partner as a customer, you "
                        "should add its VAT number."
                    )
                    % fp.display_name,
                }
            }
