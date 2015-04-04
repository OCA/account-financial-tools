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

from openerp.osv import orm, fields


class AccountConfigSettings(orm.TransientModel):
    _inherit = 'account.config.settings'

    _columns = {
        'use_journal_setting': fields.boolean(
            'Use journal setting to post journal entries '
            'on invoice and bank statement validation',),
    }

    def set_parameters(self, cr, uid, ids, context=None):
        config = self.browse(cr, uid, ids[0], context)
        config_pool = self.pool['ir.config_parameter']
        if config.use_journal_setting:
            config_pool.set_param(cr, uid, 'use_journal_setting',
                                  config.use_journal_setting)
        else:
            # remove the key from parameter
            ids = config_pool.search(cr, uid,
                                     [('key', '=', 'use_journal_setting')],
                                     context=context)
            if ids:
                config_pool.unlink(cr, uid, ids)

    def default_get(self, cr, uid, fields, context=None):
        res = super(AccountConfigSettings, self).default_get(cr, uid, fields,
                                                             context=context)
        config_pool = self.pool['ir.config_parameter']
        res['use_journal_setting'] = config_pool.get_param(
            cr, uid, 'use_journal_setting', False)
        return res
