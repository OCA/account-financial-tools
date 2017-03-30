# -*- coding: utf-8 -*-
# Copyright 2015 - Camptocamp SA - Author Vincent Renaville
# Copyright 2016 - Tecnativa - Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _
from openerp.tools import config


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def test_invoice_line_tax(self):
        errors = []
        error_template = _("Invoice has a line with product %s with no taxes")
        for invoice_line in self.mapped('invoice_line_ids'):
            if not invoice_line.invoice_line_tax_ids:
                error_string = error_template % (invoice_line.name)
                errors.append(error_string)
        if errors:
            raise exceptions.Warning(
                _('%s\n%s') % (_('No Taxes Defined!'),
                               '\n'.join(x for x in errors))
            )
        else:
            return True

    @api.multi
    def invoice_validate(self):
        if not (config['test_enable'] and
                not self.env.context.get('test_tax_required')):
            self.test_invoice_line_tax()
        res = super(AccountInvoice, self).invoice_validate()
        return res
