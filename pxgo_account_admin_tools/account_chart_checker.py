# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Pexego Sistemas Informáticos. All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
"""
Account Chart Checker Wizard
"""
__author__ = "Borja López Soilán (Pexego)"

import re
from osv import fields,osv
from tools.translate import _


class pxgo_account_chart_checker_problem(osv.osv_memory):
    """
    A problem found in the account chart
    """
    _name = "pxgo_account_admin_tools.pxgo_account_chart_checker_problem"
    _description = "Account Chart Problem"

    _columns = {
        'wizard_id': fields.many2one('pxgo_account_admin_tools.pxgo_account_chart_checker', 'Wizard', required=True, readonly=True),
        'account_id': fields.many2one('account.account', 'Account', required=True, readonly=True),
        'severity': fields.selection([('informative','Informative'), ('low','Low'), ('medium', 'Medium'), ('high','High')], 'Severity', readonly=True),
        'problem': fields.selection([
                        ('not_parent_of_children', 'Not parent of its children'),
                        ('not_children_of_parent', 'Not children of its parent'),
                    ], 'Problem', readonly=True),
        'description': fields.text('Description')
    }


    def search(self, cr, uid, args, offset=0, limit=None, order=None, context=None, count=False):
        """
        Redefinition of the search method (as osv_memory wizards currently don't
        support domain filters by themselves.
        """
        problem_ids = super(pxgo_account_chart_checker_problem, self).search(cr, uid, args, offset=offset, limit=limit, order=order, context=context, count=count)

        for arg in args:
            if arg[0] == 'wizard_id' and arg[1] == '=':
                wizard_id = arg[2]
                problems = self.browse(cr, uid, problem_ids, context=context)
                problem_ids = [problem.id for problem in problems if problem.wizard_id.id == wizard_id]

        return problem_ids


pxgo_account_chart_checker_problem()



class pxgo_account_chart_checker(osv.osv_memory):
    """
    Account Chart Checker
    """
    _name = "pxgo_account_admin_tools.pxgo_account_chart_checker"
    _description = "Account Chart Checker Wizard"

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True),        
        'problem_ids': fields.one2many('pxgo_account_admin_tools.pxgo_account_chart_checker_problem', 'wizard_id', 'Problems'),

        'state': fields.selection([('new','New'), ('done','Done')], 'Status', readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'new',
    }


    def action_check(self, cr, uid, ids, context=None):
        """
        Checks the account chart and reports the problems it finds.
        """
        for wiz in self.browse(cr, uid, ids, context):
            problems = []

            account_ids = self.pool.get('account.account').search(cr, uid, [], context=context)

            for account in self.pool.get('account.account').browse(cr, uid, account_ids, context=context):
                self._check_parent_of_children(cr, uid, account, problems)
                self._check_child_of_parent(cr, uid, account, problems)

            self.write(cr, uid, [wiz.id], { 
                    'problem_ids': [(0, 0, problem) for problem in problems] or None,
                    'state': 'done'
                })

        #
        # Return the next view: Show the problems
        #
        model_data_ids = self.pool.get('ir.model.data').search(cr, uid, [
                    ('model','=','ir.ui.view'),
                    ('module','=','pxgo_account_admin_tools'),
                    ('name','=','pxgo_account_chart_checker_problem_tree')
                ])
        resource_id = self.pool.get('ir.model.data').read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']

        return {
            'name': _("Problems Found in the Chart of Accounts"),
            'type': 'ir.actions.act_window',
            'res_model': 'pxgo_account_admin_tools.pxgo_account_chart_checker_problem',
            'view_type': 'form',
            'view_mode': 'tree',
            'views': [(resource_id, 'tree')],
            'domain': "[('wizard_id', '=', %s)]" % wiz.id,
            'context': context,
        }
        

    def _check_parent_of_children(self, cr, uid, account, problems=[], context=None):
        """
        Checks that for a parent account, every children has that account
        as its parent.
        """
        query = """
                SELECT id FROM account_account WHERE parent_left > %s and parent_right < %s
                AND COALESCE(parent_id,0) NOT IN (SELECT id FROM account_account WHERE parent_left > %s and parent_right < %s)
                AND COALESCE(parent_id,0) != %s
                """
        cr.execute(query, (account.parent_left or 0, account.parent_right or 0, account.parent_left or 0, account.parent_right or 0, account.id))
        problematic_ids = filter(None, map(lambda x:x[0], cr.fetchall()))

        for child in self.pool.get('account.account').browse(cr, uid, problematic_ids, context=context):
            problems.append({
                'problem': 'not_parent_of_children',
                'severity': 'high',
                'account_id': account.id,
                'description': _('The account %d (%s) is listed as children of %d (%s) in the preordered tree, but its parent is %d (%s)') \
                                % (child.id, child.code, account.id, account.code, child.parent_id and child.parent_id.id, child.parent_id and child.parent_id.code)
            })


    def _check_child_of_parent(self, cr, uid, account, problems=[], context=None):
        """
        Checks that for a child account, his parent has that account
        in its children.
        """
        query = """
                SELECT id FROM account_account WHERE parent_left < %s and parent_right > %s
                """
        cr.execute(query, (account.parent_left or 0, account.parent_right or 0))
        parent_ids = filter(None, map(lambda x:x[0], cr.fetchall()))

        if account.parent_id and (account.parent_id.id not in parent_ids):
            problems.append({
                'problem': 'not_children_of_parent',
                'severity': 'high',
                'account_id': account.id,
                'description': _('The account %d (%s) is children of %d (%s), but is not listed as its children on the preordered tree') \
                                % (account.id, account.code, account.parent_id.id, account.parent_id.code)
            })
        elif parent_ids and not account.parent_id:
            problems.append({
                'problem': 'not_children_of_parent',
                'severity': 'high',
                'account_id': account.id,
                'description': _('The account %d (%s) is a top level account, but is listed as a child on the preordered tree') \
                                % (account.id, account.code)
            })



pxgo_account_chart_checker()


