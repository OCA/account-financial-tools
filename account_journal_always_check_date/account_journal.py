# -*- encoding: utf-8 -*-
##############################################################################
#
#    Account Journal Always Check Date module for OpenERP
#    Copyright (C) 2013 Akretion (http://www.akretion.com)
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

from openerp.osv import orm
from openerp.tools.translate import _


class account_journal(orm.Model):
    _inherit = 'account.journal'

    def __init__(self, pool, cr):
        '''Activate 'Check Date in Period' on all existing journals'''
        init_res = super(account_journal, self).__init__(pool, cr)
        cr.execute("UPDATE account_journal SET allow_date=True")
        return init_res

    _defaults = {
        'allow_date': True,
        }

    def _allow_date_always_active(self, cr, uid, ids):
        for journal in self.browse(cr, uid, ids):
            if not journal.allow_date:
                raise orm.except_orm(
                    _('Error:'),
                    _("The option 'Check Date in Period' must be active "
                    "on journal '%s'.")
                    % journal.name)
        return True

    _constraints = [
        (_allow_date_always_active, "Error msg in raise", ['allow_date']),
    ]
