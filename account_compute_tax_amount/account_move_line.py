# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2013-2014 Camptocamp (http://www.camptocamp.com)
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

    # We set the tax_amount readonly, because we recompute it in every case.
    tax_amount = fields.Float(readonly=True)

    @api.multi
    def force_compute_tax_amount(self):
        for rec in self:
            if rec.tax_code_id:
                rec.tax_amount = rec.credit - rec.debit

    @api.model
    def create(self, vals, check=True):
        record_id = super(AccountMoveLine, self).create(vals, check=check)
        record_id.force_compute_tax_amount()
        return record_id

    @api.multi
    def write(self, vals, check=True, update_check=True):
        result = super(AccountMoveLine, self).write(
            vals,
            check=check,
            update_check=update_check)
        if ('debit' in vals) or ('credit' in vals):
            self.force_compute_tax_amount()
        return result
