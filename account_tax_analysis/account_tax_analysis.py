# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2013 Camptocamp SA
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
from osv import orm, osv, fields
from tools.translate import _


class account_tax_declaration_analysis(orm.TransientModel):
    _name = 'account.vat.declaration.analysis'
    _description = 'Account Vat Declaration'
    _columns = {
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscalyear',
                                         help='Fiscalyear to look on', required=True),

        'period_list': fields.many2many('account.period', 'account_tax_period_rel',
                                        'tax_analysis', 'period_id',
                                        'Period _list', required=True),

    }

    def create_vat(self, cr, uid, ids, context=None):
        mod_obj = self.pool.get('ir.model.data')
        action_obj = self.pool.get('ir.actions.act_window')
        domain = []
        data = self.read(cr, uid, ids, [])[0]
        period_list = data['period_list']
        if period_list:
            domain = [('period_id', 'in', period_list)]
        else:
            raise osv.except_osv(_('No period defined'), _("You must selected period "))
        ##
        actions = mod_obj.get_object_reference(cr, uid,
                                               'account_tax_analysis', 'action_view_tax_analysis')
        id_action = actions and actions[1] or False
        action_mod = action_obj.read(cr, uid, id_action)
        action_mod['domain'] = domain

        return action_mod

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
