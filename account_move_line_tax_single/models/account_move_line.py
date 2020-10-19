# Copyright 2020 CorporateHub (https://corporatehub.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    tax_id = fields.Many2one(
        string="Tax Applied",
        comodel_name="account.tax",
        domain=["|", ("active", "=", False), ("active", "=", True)],
        compute="_compute_tax_id",
        inverse="_inverse_tax_id",
        store=True,
    )

    @api.multi
    @api.depends("tax_ids")
    def _compute_tax_id(self):
        for line in self:
            line.tax_id = line.tax_ids[:1]

    @api.multi
    def _inverse_tax_id(self):
        for line in self:
            if len(line.tax_ids) > 1:
                _logger.warning(
                    _(
                        "Account Move Line #%s has more than one tax applied!"
                    ) % (
                        line.id,
                    )
                )
                line.tax_ids |= line.tax_id
                continue
            line.tax_ids = line.tax_id

    @api.constrains("tax_ids")
    def _validate_single_tax(self):
        if self.env.context.get("skip_validate_single_tax"):
            return
        if self.filtered(lambda line: len(line.tax_ids) > 1):
            raise ValidationError(_("Only single tax per line is allowed."))
