# -*- coding: utf-8 -*-
# © 2015 Vincent Renaville (Camptocamp).
# © 2017 Kitti U. (ecosoft.co.th).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, api, _
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def test_invoice_line_tax(self):
        errors = []
        error_template = _("Invoice has a line with product %s with no taxes")
        for invoice in self:
            for invoice_line in invoice.invoice_line_ids:
                if not invoice_line.invoice_line_tax_ids:
                    error_string = error_template % (invoice_line.name)
                    errors.append(error_string)
        if errors:
            errors_full_string = ',\n'.join(x for x in errors)
            raise ValidationError(errors_full_string)
        else:
            return True

    @api.multi
    def invoice_validate(self):
        self.test_invoice_line_tax()
        res = super(AccountInvoice, self).invoice_validate()
        return res
