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
from openerp.tools.translate import _


class res_company(orm.Model):
    """override company to add currency update"""

    def _multi_curr_enable(self, cr, uid, ids, field_name, arg, context=None):
        "check if multi company currency is enabled"
        result = {}
        field_ids = self.pool.get('ir.model.fields').search(
            cr, uid,
            [('name', '=', 'company_id'),
             ('model', '=', 'res.currency')]
        )
        if not field_ids:
            enable = 0
        else:
            enable = 1
        for id in ids:
            result[id] = enable
        return result

    def button_refresh_currency(self, cr, uid, ids, context=None):
        """Refresh  the currency for all the company now"""
        currency_updater_obj = self.pool.get('currency.rate.update')
        errors = currency_updater_obj.run_currency_update(
            cr, uid, context=context
        )
        if errors:
            raise orm.except_orm(
                _("Error"),
                _("Errors occurred during update:\n") + "\n".join(errors),
            )
        return True

    def on_change_auto_currency_up(self, cr, uid, id, value):
        """handle the activation of the currency update on companies.
        There are two ways of implementing multi_company currency,
        the currency is shared or not. The module take care of the two
        ways. If the currency are shared, you will only be able to set
        auto update on one company, this will avoid to have non-useful cron
        object running.
        If yours currency are not share you will be able to activate the
        auto update on each separated company

        """

        if len(id):
            id = id[0]
        else:
            return {}
        enable = self.browse(cr, uid, id).multi_company_currency_enable
        companies = self.search(cr, uid, [])
        activate_cron = 'f'
        if not value:
            # this statement is here because we do no want to save
            # in case of error
            self.write(cr, uid, id, {'auto_currency_up': value})
            for comp in companies:
                if self.browse(cr, uid, comp).auto_currency_up:
                    activate_cron = 't'
                    break
            self.pool.get('currency.rate.update').save_cron(
                cr,
                uid,
                {'active': activate_cron}
            )
            return {}
        else:
            for comp in companies:
                if comp != id and not enable:
                    current = self.browse(cr, uid, comp)
                    if current.multi_company_currency_enable:
                        # We ensure that we did not have write a true value
                        self.write(cr, uid, id, {'auto_currency_up': False})
                        msg = ('You can not activate auto currency'
                               'update on more thant one company with this '
                               'multi company configuration')
                        return {
                            'value': {'auto_currency_up': False},

                            'warning': {
                                'title': "Warning",
                                'message': msg,
                            }
                        }
            self.write(cr, uid, id, {'auto_currency_up': value})
            for comp in companies:
                if self.browse(cr, uid, comp).auto_currency_up:
                    activate_cron = 't'
                self.pool.get('currency.rate.update').save_cron(
                    cr,
                    uid,
                    {'active': activate_cron}
                )
                break
            return {}

    def on_change_interval(self, cr, uid, id, interval):
        # Function that will update the cron freqeuence
        self.pool.get('currency.rate.update').save_cron(
            cr,
            uid,
            {'interval_type': interval}
        )
        compagnies = self.search(cr, uid, [])
        for comp in compagnies:
            self.write(cr, uid, comp, {'interval_type': interval})
        return {}

    _inherit = "res.company"
    _columns = {
        # Activate the currency update
        'auto_currency_up': fields.boolean(
            'Automatic update of the currency this company'
        ),
        'services_to_use': fields.one2many(
            'currency.rate.update.service',
            'company_id',
            'Currency update services'
        ),
        # Predefine cron frequency
        'interval_type': fields.selection(
            [
                ('days', 'Day(s)'),
                ('weeks', 'Week(s)'),
                ('months', 'Month(s)')
            ],
            'Currency update frequency',
            help="Changing this value will "
                 "also affect other companies"
        ),
        # Function field that allows to know the
        # multi company currency implementation
        'multi_company_currency_enable': fields.function(
            _multi_curr_enable,
            method=True,
            type='boolean',
            string="Multi company currency",
            help="If this case is not check you can"
                 " not set currency is active on two company"
        ),
    }
