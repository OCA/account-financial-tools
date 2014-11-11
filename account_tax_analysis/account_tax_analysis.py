# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2013-2014 Camptocamp SA
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
from openerp import models, fields, api, exceptions, _


class AccountTaxDeclarationAnalysis(models.TransientModel):
    _name = 'account.vat.declaration.analysis'
    _description = 'Account Vat Declaration'

    fiscalyear_id = fields.Many2one(
        comodel_name='account.fiscalyear',
        string='Fiscalyear',
        help='Fiscalyear to look on',
        required=True,
    )

    period_list = fields.Many2many(
        comodel_name='account.period',
        relation='account_tax_period_rel',
        column1='tax_analysis',
        column2='period_id',
        string='Periods',
        required=True,
    )

    @api.multi
    def show_vat(self):
        action_obj = self.env['ir.actions.act_window']
        if not self.period_list:
            raise exceptions.Warning(_("You must select periods"))
        domain = [('period_id', 'in', self.period_list.ids)]
        action = self.env.ref('account_tax_analysis.action_view_tax_analysis')
        action_fields = action.read()[0]
        action_fields['domain'] = domain
        return action_fields
