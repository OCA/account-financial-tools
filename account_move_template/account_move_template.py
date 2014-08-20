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

from openerp.osv import fields, orm


class account_move_template(orm.Model):

    _inherit = 'account.document.template'
    _name = 'account.move.template'

    _columns = {
        'company_id': fields.many2one(
            'res.company',
            'Company',
            required=True,
            change_default=True
        ),
        'template_line_ids': fields.one2many(
            'account.move.template.line',
            'template_id',
            'Template Lines'
        ),
        'cross_journals': fields.boolean('Cross-Journals'),
        'transitory_acc_id': fields.many2one(
            'account.account',
            'Transitory account',
            required=False
        ),
    }

    def _get_default(self, cr, uid, context=None):
        self.pool.get('res.company')._company_default_get(
            cr, uid, 'account.move.template', context=context
        )
    _defaults = {
        'company_id': _get_default
    }

    def _check_different_journal(self, cr, uid, ids, context=None):
        # Check that the journal on these lines are different/same in the case
        # of cross journals/single journal
        journal_ids = []
        all_journal_ids = []
        move_template = self.pool.get('account.move.template').browse(
            cr, uid, ids)[0]
        if not move_template.template_line_ids:
            return True
        for template_line in move_template.template_line_ids:
            all_journal_ids.append(template_line.journal_id.id)
            if template_line.journal_id.id not in journal_ids:
                journal_ids.append(template_line.journal_id.id)
        if move_template.cross_journals:
            return len(all_journal_ids) == len(journal_ids)
        else:
            return len(journal_ids) == 1

    _constraints = [
        (_check_different_journal,
         'If the template is "cross-journals", the Journals must be different,'
         'if the template does not "cross-journals" '
         'the Journals must be the same!',
         ['journal_id'])
    ]


class account_move_template_line(orm.Model):
    _name = 'account.move.template.line'
    _inherit = 'account.document.template.line'

    _columns = {
        'journal_id': fields.many2one(
            'account.journal',
            'Journal',
            required=True
        ),
        'account_id': fields.many2one(
            'account.account',
            'Account',
            required=True,
            ondelete="cascade"
        ),
        'move_line_type': fields.selection(
            [('cr', 'Credit'),
             ('dr', 'Debit')],
            'Move Line Type',
            required=True
        ),
        'analytic_account_id': fields.many2one(
            'account.analytic.account',
            'Analytic Account',
            ondelete="cascade"
        ),
        'template_id': fields.many2one('account.move.template', 'Template'),
        'account_tax_id': fields.many2one('account.tax', 'Tax'),
    }

    _sql_constraints = [
        ('sequence_template_uniq', 'unique (template_id,sequence)',
         'The sequence of the line must be unique per template !')
    ]
