# Copyright 2018 Forest and Biomass Romania
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _convert_prepared_anglosaxon_line(self, line, partner):
        res = super(ProductProduct, self)._convert_prepared_anglosaxon_line(
            line, partner)
        credit = debit = 0.0
        invoice = self.env['account.invoice']
        if 'invoice_id' in line:
            invoice = self.env['account.invoice'].browse(
                line.get('invoice_id', False))
        if invoice and invoice.journal_id.posting_policy == 'storno':
            if invoice.type in ('out_invoice', 'in_refund'):
                if line.get('type', 'src') == 'dest':
                    # for OUT_invoice dest (tot. amount goes to debit)
                    debit = line['price']
                else:  # in('src','tax')
                    credit = line['price'] * (-1)
            else:  # in ('in_invoice', 'in_refund')
                if line.get('type', 'src') == 'dest':
                    credit = line['price'] * (-1)
                else:
                    debit = line['price']
            res['debit'] = debit
            res['credit'] = credit
        return res
