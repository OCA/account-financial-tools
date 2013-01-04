# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
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

from openerp.osv import fields,osv
import time
from openerp.tools.translate import _

class wizard_select_template(osv.osv_memory):

    _name = "wizard.select.move.template"
    _columns = {
        'template_id': fields.many2one('account.move.template', 'Move Template', required=True),
        'partner_id': fields.many2one('res.partner', 'Partner'),
        'line_ids': fields.one2many('wizard.select.move.template.line', 'template_id', 'Lines'),
        'state': fields.selection([
            ('template_selected','Template selected'),
            ], 'State'),
    }

    def on_change_template_id(self, cr, uid, ids, template_id):
        res = {}
        if template_id:
            res['value'] = {'line_ids': []}
            template_pool = self.pool.get('account.move.template')
            template = template_pool.browse(cr, uid, template_id)
            for line in template.template_line_ids:
                if line.type == 'input':
                    res['value']['line_ids'].append({
                        'sequence': line.sequence,
                        'name': line.name,
                        'account_id': line.account_id.id,
                        'move_line_type': line.move_line_type,
                        })
        return res
    
    def load_lines(self, cr, uid, ids, context=None):
        wizard =  self.browse(cr, uid, ids, context=context)[0]
        template_pool = self.pool.get('account.move.template')
        wizard_line_pool = self.pool.get('wizard.select.move.template.line')
        template = template_pool.browse(cr, uid, wizard.template_id.id)
        for line in template.template_line_ids:
            if line.type == 'input':
                wizard_line_pool.create(cr, uid,{
                    'template_id': wizard.id,
                    'sequence': line.sequence,
                    'name': line.name,
                    'amount': 0.0,
                    'account_id': line.account_id.id,
                    'move_line_type': line.move_line_type,
                    })
        if not wizard.line_ids:
            return self.load_template(cr, uid, ids)
        wizard.write({'state': 'template_selected'})
        return True
        
    def load_template(self, cr, uid, ids, context=None):
        template_obj = self.pool.get('account.move.template')
        template_line_obj = self.pool.get('account.move.template.line')
        account_period_obj = self.pool.get('account.period')
        
        
        mod_obj = self.pool.get('ir.model.data')
        wizard =  self.browse(cr, uid, ids, context=context)[0]
        if not template_obj.check_zero_lines(cr, uid, wizard):
            raise osv.except_osv(_('Error !'), _('At least one amount has to be non-zero!'))
        input_lines = {}

        for template_line in wizard.line_ids:
            input_lines[template_line.sequence] = template_line.amount

        period_id = account_period_obj.find(cr, uid, context=context)
        if not period_id:
            raise osv.except_osv(_('No period found !'), _('Unable to find a valid period !'))
        period_id = period_id[0]

        computed_lines = template_obj.compute_lines(cr, uid, wizard.template_id.id, input_lines)

        moves={}
        for line in wizard.template_id.template_line_ids:
            if line.journal_id.id not in moves:
                moves[line.journal_id.id]=self._make_move(
                    cr,uid,wizard.template_id.name,period_id,line.journal_id.id, wizard.partner_id.id)
        
            id_line=self._make_move_line(cr,uid,line,computed_lines,moves[line.journal_id.id],period_id,
                wizard.partner_id.id)
            if wizard.template_id.cross_journals :
                trans_account_id=wizard.template_id.transitory_acc_id.id
                id_trans_line=self._make_transitory_move_line(cr,uid,line,computed_lines,
                    moves[line.journal_id.id],period_id,trans_account_id, wizard.partner_id.id)
        
        return {
            'domain': "[('id','in', "+str(moves.values())+")]",
            'name': 'Entries',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
    #'res_id': moves.values() or False,
    def _make_move(self, cr, uid,ref,period_id,journal_id, partner_id):
        account_move_obj = self.pool.get('account.move')
        move_id = account_move_obj.create(cr, uid, {
            'ref': ref,
            'period_id': period_id,
            'journal_id': journal_id,
            'partner_id': partner_id,
        })
        return move_id
        
    def _make_move_line(self,cr,uid,line,computed_lines,move_id,period_id, partner_id):
        account_move_line_obj = self.pool.get('account.move.line')
        analytic_account_id = False
        if line.analytic_account_id:
            if not line.journal_id.analytic_journal_id:
                raise osv.except_osv(_('No Analytic Journal !'),
                    _("You have to define an analytic journal on the '%s' journal!")
                    % (line.journal_id.name,))
            analytic_account_id = line.analytic_account_id.id
        val = {
            'name': line.name,
            'move_id': move_id,
            'journal_id': line.journal_id.id,
            'period_id': period_id,
            'analytic_account_id': analytic_account_id,
            'account_id': line.account_id.id,
            'date': time.strftime('%Y-%m-%d'),
            'account_tax_id': line.account_tax_id.id,
            'credit': 0.0,
            'debit': 0.0,
            'partner_id': partner_id,
        }
        if line.move_line_type == 'cr':
            val['credit'] = computed_lines[line.sequence]
        if line.move_line_type == 'dr':
            val['debit'] = computed_lines[line.sequence]
        id_line = account_move_line_obj.create(cr, uid, val)
        return id_line
    
    def _make_transitory_move_line(
        self,cr,uid,line,computed_lines,move_id,period_id,trans_account_id, partner_id):
        account_move_line_obj = self.pool.get('account.move.line')
        analytic_account_id = False
        if line.analytic_account_id:
            if not line.journal_id.analytic_journal_id:
                raise osv.except_osv(_('No Analytic Journal !'),
                    _("You have to define an analytic journal on the '%s' journal!")
                    % (wizard.template_id.journal_id.name,))
            analytic_account_id = line.analytic_account_id.id
        val = {
            'name': 'transitory',
            'move_id': move_id,
            'journal_id': line.journal_id.id,
            'period_id': period_id,
            'analytic_account_id': analytic_account_id,
            'account_id': trans_account_id,
            'date': time.strftime('%Y-%m-%d'),
            'partner_id': partner_id,
        }
        if line.move_line_type != 'cr':
            val['credit'] = computed_lines[line.sequence]
        if line.move_line_type != 'dr':
            val['debit'] = computed_lines[line.sequence]
        id_line = account_move_line_obj.create(cr, uid, val)
        return id_line
        
wizard_select_template()

class wizard_select_template_line(osv.osv_memory):
    _description = 'Template Lines'
    _name = "wizard.select.move.template.line"
    _columns = {
        'template_id': fields.many2one('wizard.select.move.template', 'Template'),
        'sequence': fields.integer('Number', required=True),
        'name': fields.char('Name', size=64, required=True, readonly=True),
        'account_id': fields.many2one('account.account', 'Account', required=True, readonly=True),
        'move_line_type':fields.selection([
            ('cr','Credit'),
            ('dr','Debit'),
            ], 'Move Line Type', required=True,readonly=True),
        'amount': fields.float('Amount', required=True),
    }

wizard_select_template_line()
