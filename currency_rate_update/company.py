# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2009 CamptoCamp. All rights reserved.
#    @author Nicolas Bessi
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
from openerp.osv import fields, orm


class res_company(orm.Model):
    """override company to add currency update"""

    def button_refresh_currency(self, cr, uid, ids, context=None):
        """Refrech  the currency for all the company now"""
        currency_updater_obj = self.pool.get('currency.rate.update')
        currency_updater_obj.run_currency_update(cr, uid)
        return True

    def write(self, cr, uid, ids, vals, context=None):
        res = super(res_company, self).write(cr, uid, ids, vals, context=context)
        company = self.browse(cr, uid, ids)
        self.pool.get('currency.rate.update').save_cron(
            cr,
            uid,
            {'interval_type': company.interval_type}
        )
        self.pool.get('currency.rate.update').save_cron(
            cr,
            uid,
            {'active': company.auto_currency_up}
        )
        return res

    _inherit = "res.company"
    _columns = {
        # Activate the currency update
        'auto_currency_up': fields.boolean(
            'Automatical update of the currency this company'
        ),
        'services_to_use': fields.one2many(
            'currency.rate.update.service',
            'company_id',
            'Currency update services'
        ),
        # Predifine cron frequence
        'interval_type': fields.selection(
            [
                ('days', 'Day(s)'),
                ('weeks', 'Week(s)'),
                ('months', 'Month(s)')
            ],
            'Currency update frequence',
            help="Changing this value will "
                 "also affect other compagnies"
        ),
    }
