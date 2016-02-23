# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 ONESTEiN BV (<http://www.onestein.nl>).
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

from openerp.osv import fields, osv
from openerp import tools


class account_invoice_report(osv.osv):
    _inherit = "account.invoice.report"
    _columns = {
        'cost_center_id': fields.many2one('account.cost.center', string="Cost Center", readonly=True),
        'account_analytic_id': fields.many2one('account.analytic.account', string="Analytic Account", readonly=True)
    }

    def _select(self):
        return super(account_invoice_report, self)._select() + \
            ", sub.cost_center_id as cost_center_id, sub.account_analytic_id as account_analytic_id"

    def _sub_select(self):
        return super(account_invoice_report, self)._sub_select() + \
            ", ail.cost_center_id as cost_center_id, ail.account_analytic_id as account_analytic_id"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + \
            ", ail.cost_center_id, ail.account_analytic_id"
