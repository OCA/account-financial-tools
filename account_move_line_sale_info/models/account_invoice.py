# Copyright 2020 ForgeFlow S.L.
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
                if line.sale_line_ids and len(line.sale_line_ids) == 1:
                    move_line_dict['sale_line_id'] = line.sale_line_ids[0].id
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super(AccountInvoice, self).line_get_convert(line, part)
        if line.get('sale_line_id', False):
            res['sale_line_id'] = line.get('sale_line_id')
        return res

    @api.model
    def _anglo_saxon_sale_move_lines(self, i_line):
        """
        We need to add the sale_line to those entries too
        """
        res = super()._anglo_saxon_sale_move_lines(i_line)
        for aml in res:
            if i_line.sale_line_ids and len(i_line.sale_line_ids) == 1:
                aml['sale_line_id'] = i_line.sale_line_ids[0].id
        return res
