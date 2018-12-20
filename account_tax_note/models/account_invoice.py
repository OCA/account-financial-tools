# Copyright 2018 Creu Blanca
# Copyright 2018 Eficent Business and IT Consulting Services, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_notes_by_tax(self):
        self.ensure_one()
        return [(t.name, t.note) for t in self.tax_line_ids.mapped('tax_id')]
