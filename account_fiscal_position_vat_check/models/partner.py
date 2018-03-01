# © 2013-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('property_account_position_id')
    def onchange_fiscal_position(self):
        """Warning if the fiscal position requires a VAT number and the
        partner doesn't have one yet"""
        fiscal_position = self.property_account_position_id
        if fiscal_position.vat_required and self.customer and not self.vat:
            return {
                'warning': {
                    'title': _('Missing VAT number:'),
                    'message': _(
                        "You have set the fiscal position '%s' "
                        "that require the customer to have a VAT number, "
                        "but the VAT number is missing."
                    ) % fiscal_position.name
                }
            }
