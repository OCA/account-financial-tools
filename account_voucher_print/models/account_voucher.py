# Copyright 2020 Sergio Zanchetta (Associazione PNLUG - Gruppo Odoo)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models, api, _


class AccountVoucher(models.Model):
    _inherit = "account.voucher"

    amount_in_words = fields.Char("Amount In Words", compute="_compute_amount_in_words")

    @api.multi
    def _get_report_base_filename(self):
        self.ensure_one()
        return \
            self.voucher_type == 'sale' and \
            self.state == 'draft' and \
            _('Draft Receipt') or \
            self.voucher_type == 'sale' and \
            self.state in ('proforma', 'posted') and \
            _('Receipt - %s') % (self.number) or \
            self.voucher_type == 'purchase' and \
            self.state == 'draft' and \
            _('Draft Purchase Receipt') or \
            self.voucher_type == 'purchase' and \
            self.state in ('proforma', 'posted') and \
            _('Purchase Receipt - %s') % (self.number)

    @api.depends('amount')
    def _compute_amount_in_words(self):
        for receipt in self:
            receipt.amount_in_words = receipt.currency_id.amount_to_text(receipt.amount)

    @api.multi
    def receipt_print(self):
        """Print the receipt"""
        return self.env.ref(
            'account_voucher_print.account_receipts').report_action(self, data='')
