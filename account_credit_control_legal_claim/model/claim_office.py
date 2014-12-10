# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from openerp import models, fields


class ClaimOffice(models.Model):
    """Claim office"""

    _name = "legal.claim.office"

    name = fields.Char(required=True)
    locations_ids = fields.One2many(comodel_name='res.better.zip',
                                    inverse_name='claim_office_id',
                                    string='Related zip')
    fees_scheme_id = fields.Many2one(comodel_name='legal.claim.fees.scheme',
                                     string='Fees Scheme',
                                     select=True,
                                     required=True)
    partner_id = fields.Many2one(comodel_name='res.partner',
                                 string='Office Address',
                                 required=True)


class BetterZip(models.Model):
    """Add relation to claim office"""

    _inherit = "res.better.zip"
    claim_office_id = fields.Many2one(comodel_name='legal.claim.office',
                                      string='Claim office',
                                      select=True)
