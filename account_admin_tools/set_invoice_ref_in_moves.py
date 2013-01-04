# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
"""
Set Invoice Reference in Moves
"""
__author__ = "Borja López Soilán (Pexego)"

import re
from osv import fields, osv
from tools.translate import _


class set_invoice_ref_in_moves(osv.osv_memory):
    """
    Set Invoice Reference in Moves

    Searchs for account moves associated with invoices that do not have the
    right reference (the reference from a supplier invoice or the number from
    a customer invoice) and lets the user fix them.
    """
    _name = "account_admin_tools.set_invoice_ref_in_moves"
    _description = "Set Invoice Reference in Moves"

    _columns = {
        'state': fields.selection([('new', 'New'), ('ready', 'Ready'), ('done', 'Done')], 'Status', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),
        'period_ids': fields.many2many('account.period', 'set_invoice_ref_in_moves_period_rel', 'wizard_id', 'period_id', "Periods"),
        'move_ids': fields.many2many('account.move', 'set_invoice_ref_in_move_move_rel', 'wizard_id', 'move_id', 'Moves'),
    }

    _defaults = {
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
        'move_ids': lambda self, cr, uid, context: context and context.get('move_ids', None),
        'period_ids': lambda self, cr, uid, context: context and context.get('period_ids', None),
        'state': lambda self, cr, uid, context: context and context.get('state', 'new'),
    }

    def _next_view(self, cr, uid, ids, view_name, args=None, context=None):
        """
        Return the next wizard view
        """
        if context is None:
            context = {}
        if args is None:
            args = {}
        ctx = context.copy()
        ctx.update(args)

        model_data_ids = self.pool.get('ir.model.data').search(cr, uid, [
            ('model', '=', 'ir.ui.view'),
            ('module', '=', 'account_admin_tools'),
            ('name', '=', view_name)
        ])
        resource_id = self.pool.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'name': _("Set Invoice Reference in Moves"),
            'type': 'ir.actions.act_window',
            'res_model': 'account_admin_tools.set_invoice_ref_in_moves',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(resource_id, 'form')],
            'domain': "[('id', 'in', %s)]" % ids,
            'context': ctx,
            'target': 'new',
        }

    def _get_reference(self, cr, uid, invoice, context=None):
        """
        Get's the reference for an account move given the related invoice.
        """
        if invoice.type in ('in_invoice', 'in_refund'):
            return invoice.reference

    def _is_valid_reference(self, cr, uid, reference, invoice, context=None):
        """
        Checks that the given reference matches the invoice reference or number.
        """
        if reference == invoice.reference:
            return True
        else:
            return False

    def action_skip_new(self, cr, uid, ids, context=None):
        """
        Action that just skips the to the ready state
        """
        return self._next_view(cr, uid, ids, 'view_set_invoice_ref_in_moves_ready_form', {'state': 'ready'}, context)

    def action_find_moves_with_wrong_invoice_ref(self, cr, uid, ids, context=None):
        """
        Action that searchs for account moves associated with invoices,
        that do not have the right reference.
        """
        wiz = self.browse(cr, uid, ids[0], context)

        # FIXME: The next block of code is a workaround to the lp:586252 bug of the 6.0 client.
        #        (https://bugs.launchpad.net/openobject-client/+bug/586252)
        if wiz.period_ids:
            period_ids = [period.id for period in wiz.period_ids]
        else:
            period_ids = context and context.get('period_ids')

        #
        # Find the invoices (on the given periods)
        #
        args = []
        if period_ids:
            args = [('period_id', 'in', period_ids)]
        invoice_ids = self.pool.get(
            'account.invoice').search(cr, uid, args, context=context)

        #
        # Get the moves with references not matching the desired ones
        #
        move_ids = []
        for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
            if invoice.move_id:
                if not self._is_valid_reference(cr, uid, invoice.move_id.ref, invoice, context=context):
                    reference = self._get_reference(
                        cr, uid, invoice, context=context)
                    if reference:
                        move_ids.append(invoice.move_id.id)

        #
        # Return the next view: Show 'ready' view
        #
        args = {
            'move_ids': move_ids,
            'state': 'ready',
        }
        return self._next_view(cr, uid, ids, 'view_set_invoice_ref_in_moves_ready_form', args, context)

    def action_set_invoice_ref_in_moves(self, cr, uid, ids, context=None):
        """
        Action that sets the invoice reference or number as the account move
        reference for the selected moves.
        """
        wiz = self.browse(cr, uid, ids[0], context)

        # FIXME: The next block of code is a workaround to the lp:586252 bug of the 6.0 client.
        #        (https://bugs.launchpad.net/openobject-client/+bug/586252)
        if wiz.move_ids:
            move_ids = [line.id for line in wiz.move_ids]
        else:
            move_ids = context and context.get('move_ids')

        #
        # Find the invoices of the moves
        #
        args = [('move_id', 'in', move_ids)]
        invoice_ids = self.pool.get(
            'account.invoice').search(cr, uid, args, context=context)

        #
        # Update the moves with the reference of the invoice.
        #
        for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context=context):
            if invoice.move_id:
                reference = self._get_reference(
                    cr, uid, invoice, context=context)
                if reference and invoice.move_id.ref != reference:
                    self.pool.get('account.move').write(cr, uid, [invoice.move_id.id], {'ref': reference}, context=context)

                    #
                    # Update the move line references too
                    # (if they where equal to the move reference)
                    #
                    for line in invoice.move_id.line_id:
                        if line.ref == invoice.move_id.ref:
                            self.pool.get('account.move.line').write(cr, uid, [line.id], {'ref': reference}, context=context)

        #
        # Return the next view: Show 'done' view
        #
        args = {
            'move_ids': move_ids,
            'state': 'done',
        }
        return self._next_view(cr, uid, ids, 'view_set_invoice_ref_in_moves_done_form', args, context)


set_invoice_ref_in_moves()
