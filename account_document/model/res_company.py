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
