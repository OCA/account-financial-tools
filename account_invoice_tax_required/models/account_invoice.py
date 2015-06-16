# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2015 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api, exceptions, _


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def test_invoice_line_tax(self):
        errors = []
        error_template = _("Invoice have a line with product %s with no taxes")
        for invoice in self:
            for invoice_line in invoice.invoice_line:
                if not invoice_line.invoice_line_tax_id:
                    error_string = error_template % (invoice_line.name)
                    errors.append(error_string)
        if errors:
            errors_full_string = ','.join(x for x in errors)
            raise exceptions.Warning(_('No Taxes Defined!'),
                                     errors_full_string)
        else:
            return True

    @api.multi
    def invoice_validate(self):
        self.test_invoice_line_tax()
        res = super(AccountInvoice, self).invoice_validate()
        return res
