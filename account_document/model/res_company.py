# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in module root
# directory
##############################################################################
from openerp import fields, models, api


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def _get_localizations(self):
        return []

    _localization_selection = (
            lambda self, *args, **kwargs: self._get_localizations(
                *args, **kwargs))

    vat_responsability_id = fields.Many2one(
        related='partner_id.vat_responsability_id',
        )
    localization = fields.Selection(
        _localization_selection,
        'Localization',
        )
    invoice_vat_discrimination_default = fields.Selection(
        [('no_discriminate_default', 'Yes, No Discriminate Default'),
         ('discriminate_default', 'Yes, Discriminate Default')],
        'Invoice VAT discrimination default',
        default='no_discriminate_default',
        required=True,
        help="Definie behaviour on invoices reports. Discrimination or not "
        "will depend in partner and company responsability and AFIP letters "
        "setup:\n"
        "* If No Discriminate Default, if no match found it won't discriminate"
        " by default\n"
        "* If Discriminate Default, if no match found it would discriminate by"
        " default")
