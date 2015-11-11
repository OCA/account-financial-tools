# coding=utf-8
##############################################################################
#
#    account_auto_fy_sequence module for Odoo
#    Copyright (C) 2014 ACSONE SA/NV (<http://acsone.eu>)
#    @author Laetitia Gangloff <laetitia.gangloff@acsone.eu>
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


class account_journal(orm.Model):
    _inherit = "account.journal"

    def create_sequence(self, cr, uid, vals, context=None):
        """ Create new no_gap entry sequence for every new Joural
            with fiscal year prefix
        """
        seq_id = super(account_journal, self).create_sequence(cr, uid, vals,
                                                              context=context)

        seq_obj = self.pool['ir.sequence']
        seq = seq_obj.browse(cr, uid, seq_id, context=context)
        prefix = seq.prefix.replace('%(year)s', '%(fy)s')
        seq_obj.write(cr, uid, seq_id, {'prefix': prefix}, context=context)
        return seq_id
