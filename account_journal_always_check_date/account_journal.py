# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Journal Always Check Date module for OpenERP
#    Copyright (C) 2013-2014 Akretion (http://www.akretion.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
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

from openerp import models, fields, api, _


class account_journal(models.Model):
    _inherit = 'account.journal'

    @api.v7
    def init(self, cr):
        '''Activate 'Check Date in Period' on all existing journals'''
        cr.execute(
            "UPDATE account_journal SET allow_date=true "
            "WHERE allow_date <> true")
        return True

    allow_date = fields.Boolean(default=True)

    @api.one
    @api.constrains('allow_date')
    def _allow_date_always_active(self):
        if not self.allow_date:
            raise Warning(
                _("The option 'Check Date in Period' must be active "
                    "on journal '%s'.") % self.name)
