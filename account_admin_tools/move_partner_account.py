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
Move Partner Account Wizard

Checks that the account moves use the partner account instead of a
generic account.
"""
__author__ = "Borja López Soilán (Pexego)"

import re
from osv import fields, osv
from tools.translate import _


class move_partner_account(osv.osv_memory):
    """
    Move Partner Account Wizard

    Checks that the account moves use the partner account instead of a
    generic account.
    """
    _name = "account_admin_tools.move_partner_account"
    _description = "Move Partner Account Wizard"

    _columns = {
        'state': fields.selection([('new', 'New'), ('done', 'Done')],
                                  'Status', readonly=True),
        #
        # Account move parameters
        #
        'company_id': fields.many2one('res.company', 'Company',
                                      required=True, readonly=True),
        'period_ids': fields.many2many('account.period',
                                       'move_partner_account_period_rel', 'wizard_id',
                                       'period_id', "Periods"),
        'account_payable_id': fields.many2one('account.account',
                                              'Account Payable', required=True),
        'account_receivable_id': fields.many2one('account.account',
                                                 'Account Receivable', required=True),
    }

    def _get_payable_account_id(self, cr, uid, context=None):
        """
        Gets the default payable (supplier) account property value for the
        current (user's) company.
        """
        if context is None:
            context = {}
        company_id = self.pool.get('res.users').browse(cr, uid, uid,
                                                       context).company_id.id
        res = None
        property_ids = self.pool.get('ir.property').search(cr, uid, [
            '|',
            ('company_id', '=', company_id),
            ('company_id', '=', False),
            ('name', '=', 'property_account_payable'),
            ('res_id', '=', False)
        ])
        if property_ids:
            property = self.pool.get(
                'ir.property').browse(cr, uid, property_ids[0])
            if property:
                res = property.value_reference.id
        return res

    def _get_receivable_account_id(self, cr, uid, context=None):
        """
        Gets the default receivable (customer) account property value for the
        current (user's) company.
        """
        company_id = self.pool.get('res.users').browse(cr, uid, uid,
                                                       context).company_id.id
        res = None
        property_ids = self.pool.get('ir.property').search(cr, uid, [
            '|',
            ('company_id', '=', company_id),
            ('company_id', '=', False),
            ('name', '=', 'property_account_receivable'),
            ('res_id', '=', False)
        ])
        if property_ids:
            property = self.pool.get('ir.property').browse(cr, uid,
                                                           property_ids[0])
            if property:
                res = property.value_reference.id
        return res

    _defaults = {
        'company_id': lambda self, cr, uid, context:
        self.pool.get('res.users').browse(cr, uid, uid,
                                          context).company_id.id,
        'account_payable_id': _get_payable_account_id,
        'account_receivable_id': _get_receivable_account_id,
    }

    def action_set_partner_accounts_in_moves(self, cr, uid, ids, context=None):
        """
        Action that searchs for the account moves that do not use the partner
        account, but the generic payable/receivable one, and sets the partner
        account instead.
        """
        for wiz in self.browse(cr, uid, ids, context):
            period_ids = [period.id for period in wiz.period_ids]
            query_acc = """
                    UPDATE account_move_line
                    SET account_id=%s
                    WHERE partner_id=%s
                          AND account_id=%s
                    """
            query_inv = """
                    UPDATE account_invoice
                    SET account_id=%s
                    WHERE partner_id=%s
                          AND account_id=%s
                    """
            periods_str = ','.join(map(str, period_ids))
            if period_ids:
                query_acc += """      AND period_id IN (%s)""" % periods_str
                query_inv += """      AND period_id IN (%s)""" % periods_str

            partner_ids = self.pool.get('res.partner').search(cr, uid, [])
            for partner in self.pool.get('res.partner').browse(cr, uid, partner_ids):
                # Receivable account
                if partner.property_account_receivable.id != wiz.account_receivable_id.id:
                    cr.execute(query_acc % (partner.property_account_receivable.id, partner.id, wiz.account_receivable_id.id))
                    cr.execute(query_inv % (partner.property_account_receivable.id, partner.id, wiz.account_receivable_id.id))
                # Payable account
                if partner.property_account_payable.id != wiz.account_payable_id.id:
                    cr.execute(query_acc % (partner.property_account_payable.id, partner.id, wiz.account_payable_id.id))
                    cr.execute(query_inv % (partner.property_account_payable.id, partner.id, wiz.account_payable_id.id))

            # Update the wizard status
            self.write(cr, uid, [wiz.id], {'state': 'done'})

        #
        # Return the next view: Show 'done' view
        #
        model_data_ids = self.pool.get('ir.model.data').search(cr, uid, [
            ('model', '=', 'ir.ui.view'),
            ('module', '=', 'account_admin_tools'),
            ('name', '=', 'view_move_partner_account_done_form')
        ])
        resource_id = self.pool.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

        return {
            'name': _("Set Partner Accounts in Moves"),
            'type': 'ir.actions.act_window',
            'res_model': 'account_admin_tools.move_partner_account',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(resource_id, 'form')],
            'domain': "[('id', 'in', %s)]" % ids,
            'context': context,
            'target': 'new',
        }


move_partner_account()
