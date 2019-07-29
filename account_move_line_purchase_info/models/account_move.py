# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#           (www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    purchase_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string='Purchase Order Line',
        ondelete='set null', index=True,
    )

    purchase_id = fields.Many2one(
        comodel_name='purchase.order',
        related='purchase_line_id.order_id',
        string='Purchase Order',
        store=True, index=True,
    )
