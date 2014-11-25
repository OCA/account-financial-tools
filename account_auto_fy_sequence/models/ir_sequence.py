# coding=utf-8
##############################################################################
#
#    account_auto_fy_sequence module for Odoo
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#    @author Stéphane Bidoul <stephane.bidoul@acsone.eu>
#
#    account_auto_fy_sequence is free software:
#    you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License v3 or later
#    as published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    account_auto_fy_sequence is distributed
#    in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License v3 or later for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    v3 or later along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import orm
from openerp.tools.translate import _

FY_SLOT = '%(fy)s'


class Sequence(orm.Model):
    _inherit = 'ir.sequence'

    def _create_fy_sequence(self, cr, uid, seq, fiscalyear, context=None):
        """ Create a FY sequence by cloning a sequence
        which has %(fy)s in prefix or suffix """
        fy_seq_id = self.create(cr, uid, {
            'name': seq.name + ' - ' + fiscalyear.code,
            'code': seq.code,
            'implementation': seq.implementation,
            'prefix': (seq.prefix and
                       seq.prefix.replace(FY_SLOT, fiscalyear.code)),
            'suffix': (seq.suffix and
                       seq.suffix.replace(FY_SLOT, fiscalyear.code)),
            'number_next': 1,
            'number_increment': seq.number_increment,
            'padding': seq.padding,
            'company_id': seq.company_id.id,
        }, context=context)
        self.pool['account.sequence.fiscalyear']\
            .create(cr, uid, {
                'sequence_id': fy_seq_id,
                'sequence_main_id': seq.id,
                'fiscalyear_id': fiscalyear.id,
            }, context=context)
        return fy_seq_id

    def _next(self, cr, uid, seq_ids, context=None):
        if context is None:
            context = {}
        assert len(seq_ids) == 1
        seq = self.browse(cr, uid, seq_ids[0], context)
        if (seq.prefix and FY_SLOT in seq.prefix) or \
                (seq.suffix and FY_SLOT in seq.suffix):
            fiscalyear_id = context.get('fiscalyear_id')
            if not fiscalyear_id:
                raise orm.except_orm(_('Error!'),
                                     _('The system tried to access '
                                       'a fiscal year sequence '
                                       'without specifying the actual '
                                       'fiscal year.'))
            # search for existing fiscal year sequence
            for line in seq.fiscal_ids:
                if line.fiscalyear_id.id == fiscalyear_id:
                    return super(Sequence, self)\
                        ._next(cr, uid, [line.sequence_id.id], context)
            # no fiscal year sequence found, auto create it
            fiscalyear = self.pool['account.fiscalyear']\
                .browse(cr, uid, fiscalyear_id, context=context)
            fy_seq_id = self._create_fy_sequence(cr, uid, seq,
                                                 fiscalyear, context)
            return super(Sequence, self)\
                ._next(cr, uid, [fy_seq_id], context)
        return super(Sequence, self)._next(cr, uid, seq_ids, context)
