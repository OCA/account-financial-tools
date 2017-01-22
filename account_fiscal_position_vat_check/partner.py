# -*- coding: utf-8 -*-
# © 2013-2016 Akretion (Alexis de Lattre <alexis.delattre@akretion.com>)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.onchange('property_account_position')
    def fiscal_position_change(self):
        """Warning if the fiscal position requires a VAT number and the
        partner doesn't have one yet"""
        fp = self.property_account_position
        if fp.customer_must_have_vat and self.customer and not self.vat:
            return {
                'warning': {
                    'title': _('Missing VAT number:'),
                    'message': _(
                        "You have set the fiscal position '%s' "
                        "that require the customer to have a VAT number, "
                        "but the VAT number is missing.") % fp.name
                }
            }
