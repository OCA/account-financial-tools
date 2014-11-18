# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013 Camptocamp (http://www.camptocamp.com)
# All Right Reserved
#
# Author : Vincent Renaville (Camptocamp)
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

from openerp import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # We set the tax_amount invisible, because we recompute it in every case.
    tax_amount = fields.Float(invisible=True)

    @api.one
    def force_compute_tax_amount(self):
        if self.tax_code_id:
            self.tax_amount = self.credit - self.debit

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
        record = super(AccountMoveLine, self).create(vals)
        record.force_compute_tax_amount()
        return record

    @api.multi
    def write(self, vals):
        result = super(AccountMoveLine, self).write(vals)
        if ('debit' in vals) or ('credit' in vals):
            self.force_compute_tax_amount()
        return result
