# -*- coding: utf-8 -*-
# © 2016 Matthieu Dietrich, Vincent Renaville
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import models, fields


class AccountStatementOperationTemplate(models.Model):
    _inherit = "account.statement.operation.template"

    tax_id = fields.Many2one(
        comodel_name='account.tax', string='Tax', ondelete='restrict',
        domain=[('parent_id', '=', False)]
    )
