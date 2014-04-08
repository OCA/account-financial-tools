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
from itertools import chain
from openerp.osv import orm, fields


class credit_control_policy_changer(orm.TransientModel):
    """Wizard that is run from invoices and allows to set manually a policy
    Policy are actually apply to related move lines availabe
    in selection widget

    """
    _name = "credit.control.policy.changer"
    _columns = {
        'new_policy_id': fields.many2one('credit.control.policy',
                                      'New Policy to Apply',
                                      required=True),
        'new_policy_level_id': fields.many2one('credit.control.policy.level',
                                            'New level to apply',
                                            required=True),
        'move_line_ids': fields.many2many('account.move.line',
                                          rel='credit_changer_ml_rel',
                                          string='Move line to change'),
    }

    def _get_default_lines(self, cr, uid, context=None):
        if context is None:
            context = {}
        active_ids = context.get('active_ids')
        selected_line_ids = []
        inv_model = self.pool['account.invoice']
        move_line_model = self.pool['account.move.line']
        if not active_ids:
            return False
            # raise ValueError('No active_ids passed in context')
        for invoice in inv_model.browse(cr, uid, active_ids, context=context):
            domain = [('account_id', '=', invoice.account_id.id),
                      ('move_id', '=', invoice.move_id.id),
                      ('reconcile_id', '=', False)]
            move_ids = move_line_model.search(cr, uid, domain, context=context)
            selected_line_ids.extend(move_ids)
        return selected_line_ids

    _defaults = {'move_line_ids': _get_default_lines}

    def _mark_as_overriden(self, cr, uid, move_lines, context=None):
        credit_model = self.pool['credit.control.line']
        domain = [('id', 'in', [x.id for x in move_lines])]
        credits_ids = credit_model.search(cr, uid, domain, context=context)
        credit_model.write(cr, uid,
                           credits_ids,
                           {'manually_overriden': True},
                           context)
        return credits_ids

    def set_new_policy(self, cr, uid, wizard_id, context=None):
        assert len(wizard_id) == 1, "Only one id expected"
        wizard_id = wizard_id[0]

        credit_line_model = self.pool['credit.control.line']
        ir_model = self.pool['ir.model.data']
        ui_act_model = self.pool['ir.actions.act_window']
        wizard = self.browse(cr, uid, wizard_id, context=context)
        controlling_date = fields.date.today()
        self._mark_as_overriden(cr,
                                uid,
                                wizard.move_line_ids,
                                context=context)
        # As disscused with business expert
        # draft line should be passed to ignored
        # if same level as the new one
        # As it is a manual action
        # We also ignore rounding tolerance
        generated_ids = credit_line_model.create_or_update_from_mv_lines(
            cr, uid, [],
            [x.id for x in wizard.move_line_ids],
            wizard.new_policy_level_id.id,
            controlling_date,
            check_tolerance=False,
            context=None
        )
        view_id = ir_model.get_object_reference(cr, uid,
                                                "account_credit_control",
                                                "credit_control_line_action")
        assert view_id, 'No view found'
        action =  ui_act_model.read(cr, uid, view_id[1], context=context)
        action['domain'] = [('id', 'in', generated_ids)]
        return action
