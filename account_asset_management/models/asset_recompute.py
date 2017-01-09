# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2014 ACSONE SA/NV (http://acsone.eu).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models


class AccountAssetRecomputeTrigger(models.Model):
    _name = 'account.asset.recompute.trigger'
    _description = "Asset table recompute triggers"

    reason = fields.Char(
        string='Reason', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True)
    date_trigger = fields.Datetime(
        'Trigger Date',
        readonly=True,
        help="Date of the event triggering the need to "
             "recompute the Asset Tables.")
    date_completed = fields.Datetime(
        'Completion Date', readonly=True)
    state = fields.Selection(
        selection=[('open', 'Open'), ('done', 'Done')],
        string='State', default='open',
        readonly=True)
