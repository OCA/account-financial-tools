# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Savoir-faire Linux
#    (<http://www.savoirfairelinux.com>).
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

from openerp.osv import orm, fields


class AccountInvoice(orm.Model):
    _name = _inherit = 'account.invoice'

    def _get_accounts_by_state(self, cr, uid, ids, context=None):
        cr.execute(
            """
            SELECT
            ai.id
            FROM account_invoice ai
            LEFT JOIN res_partner p ON ai.partner_id = p.id
            LEFT JOIN res_country_state s ON p.state_id = s.id
            WHERE s.id IN %s
            """,
            (tuple(ids), ),
        )
        return [r[0] for r in cr.fetchall()]

    def _get_partner_state_name(self, cr, uid, ids, field_name, arg,
                                context=None):
        cr.execute(
            """
            SELECT ai.id, s.name
            FROM account_invoice ai
            LEFT JOIN res_partner p ON ai.partner_id = p.id
            LEFT JOIN res_country_state s ON p.state_id = s.id
            WHERE ai.id IN %s
            """,
            (tuple(ids), ),
        )

        return dict(
            (r[0], r[1] or False)
            for r in cr.fetchall()
        )

    _columns = {
        'partner_state_name': fields.function(
            _get_partner_state_name,
            type="char",
            method=True, string="Partner State",
            store={
                "account.invoice": (
                    lambda self, cr, uid, ids, context=None: ids,
                    ['partner_id'], 10),
                "res.partner": (
                    lambda self, cr, uid, ids, context=None: (
                        self.pool["account.invoice"].search(
                            cr, uid, [('partner_id', 'in', tuple(ids))],
                            context=context,
                        )),
                    ['state_id'], 10),
                "res.country.state": (
                    _get_accounts_by_state,
                    ['name'], 10),
            }),
    }
