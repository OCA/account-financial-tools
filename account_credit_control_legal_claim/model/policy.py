# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
from openerp.tools.translate import _

class credit_control_policy_level(orm.Model):
    """Add claim type to policy level"""

    _inherit = "credit.control.policy.level"
    _columns = {
        'is_legal_claim': fields.boolean('Legal Claim Action')
    }

    def _check_legal_claim_level(self, cr, uid, ids, context=None):
        for current_level in self.browse(cr, uid, ids, context=context):
            levels = current_level.policy_id.level_ids
            highest = max(levels, key= lambda x: x.level)
            for lvl in levels:
                if lvl.is_legal_claim and lvl != highest:
                    raise orm.except_orm(
                        _('Only highest level can be tickes as legal claim'),
                        _('The current highest level is %s') % highest.name
                    )
        return True

    _constraints = [(_check_legal_claim_level,
                     'Only highest level can be legal claim',
                     ['is_legal_claim'])]
