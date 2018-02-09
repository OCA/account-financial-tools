# Copyright 2017 Eficent Business and IT Consulting Services S.L.
#           (www.eficent.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.model
    def invoice_line_move_line_get(self):
        res = super(AccountInvoice, self).invoice_line_move_line_get()

        invoice_line_model = self.env['account.invoice.line']
        for move_line_dict in res:
            if 'invl_id' in move_line_dict:
                line = invoice_line_model.browse(move_line_dict['invl_id'])
                move_line_dict['purchase_line_id'] = line.purchase_line_id.id

        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('purchase_line_id', False):
            res['purchase_line_id'] = line.get('purchase_line_id')
        return res
