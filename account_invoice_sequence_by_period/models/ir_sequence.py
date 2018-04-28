# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2015 Noviat nv/sa (www.noviat.com).
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

from openerp import models, fields


class IrSequenceFiscalyear(models.Model):
    _inherit = 'account.sequence.fiscalyear'

    period_id = fields.Many2one(
        'account.period', string='Period', ondelete='cascade')

    _sql_constraints = [
        ('period_uniq',
         'unique (sequence_id, fiscalyear_id, period_id)',
         'Duplicate Period in Fiscal Year Sequence !')
        ]


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _interpolation_dict_context(self, context=None):
        res = super(
            IrSequence, self)._interpolation_dict_context(context=context)
        if self._sequence_context.get('period'):
            p = self._sequence_context['period'].date_start[5:7]
        else:
            p = res['month']
        res.update({'p': p})
        return res

    def _interpolation_dict(self):
        """
        This method has been replaced by _interpolation_dict_context
        on 2015-08-25, cf. commit
        github.com/odoo/odoo/commit/3e82c94d695327d5fa85cf6c9eca5039d7bc1bb6
        """
        res = super(IrSequence, self)._interpolation_dict()
        if self._sequence_context.get('period'):
            p = self._sequence_context['period'].date_start[5:7]
        else:
            p = res['month']
        res.update({'p': p})
        return res

    def _next(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        self._sequence_context = {}
        if context.get('period'):
            period = context['period']
            self._sequence_context['period'] = period
            cr.execute(
                "SELECT sequence_id FROM account_sequence_fiscalyear sf "
                "JOIN ir_sequence s ON sf.sequence_main_id=s.id "
                "WHERE s.id=%s AND sf.period_id=%s",
                (ids[0], period.id))
            res = cr.fetchone()
            if res:
                return super(IrSequence, self)._next(
                    cr, uid, [res[0]], context)
        return super(IrSequence, self)._next(cr, uid, ids, context)
