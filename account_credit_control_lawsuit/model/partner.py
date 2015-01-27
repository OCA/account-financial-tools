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
from openerp import models, fields, api


class ResPartner(models.Model):
    """Add related lawsuit office"""

    _inherit = "res.partner"

    lawsuit_office_id = fields.Many2one(
        comodel_name='lawsuit.office',
        compute='_get_lawsuit_office',
        string='Lawsuit Office',
        help="The lawsuit office assigned to the partner. "
             "The office selected for a customer is the one "
             "in the same city.",
        )

    @api.depends('zip', 'city')
    def _get_lawsuit_office(self):
        location_model = self.env['res.better.zip']
        for partner in self:
            domain = [('name', '=', partner.zip),
                      ('city', '=', partner.city),
                      ('lawsuit_office_id', '!=', False)]
            location = location_model.search(domain, limit=1)
            if location:
                partner.lawsuit_office_id = location.lawsuit_office_id
