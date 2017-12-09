# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011- Slobodni programi d.o.o.
#    @author: Goran Kliska
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

from openerp.osv import fields, orm
from openerp.tools.translate import _


class account_journal(orm.Model):
    _inherit = "account.journal"
    _columns = {
        'posting_policy': fields.selection(
            [('contra', 'Contra (debit<->credit)'),
             ('storno', 'Storno (-)')],
            'Storno or Contra', required=True,
            help="Storno allows minus postings, Refunds are posted on the "
                 "same journal/account * (-1).\n"
                 "Contra doesn't allow negative posting. "
                 "Refunds are posted by swaping credit and debit side."),
        'refund_journal_id': fields.many2one(
            'account.journal',
            'Refund journal',
            help="Journal for refunds/returns from this journal. "
                 "Leave empty to use same journal for normal and "
                 "refund/return postings.")}
    _defaults = {'posting_policy': 'storno'}


class account_move_line(orm.Model):
    _inherit = "account.move.line"

    def _auto_init(self, cr, context=None):
        result = super(account_move_line, self)._auto_init(cr, context=context)
        # Drop original constraint to fit storno posting with minus.
        cr.execute("""
            DROP INDEX IF EXISTS account_move_line_credit_debit2;
        """)
        return result

    # Original constraints
    # 'credit_debit2' - 'CHECK (credit+debit>=0)' is replaced with dummy
    # constraint that is always true.

    _sql_constraints = [
        ('credit_debit2',
         'CHECK (abs(credit+debit)>=0)',
         'Wrong credit or debit value in accounting entry !'),
    ]

    def _check_contra_minus(self, cr, uid, ids, context=None):
        """ This is to restore credit_debit2 check functionality,
            for contra journals.
        """
        for l in self.browse(cr, uid, ids, context=context):
            if l.journal_id.posting_policy == 'contra':
                if l.debit + l.credit < 0.0:
                    return False
        return True

    _constraints = [
        (_check_contra_minus,
         _("Negative credit or debit amount is not allowed for 'contra' "
           "journal policy."), ['journal_id']),
    ]

    # Inherit residual function to allow amount residual according to storno
    # journals.
    def _amount_residual(self, cr, uid, ids, field_names, args, context=None):
        res = super(account_move_line, self)._amount_residual(cr,
                                                              uid,
                                                              ids,
                                                              field_names,
                                                              args,
                                                              context=context)
        if context is None:
            context = {}
        for move_line in self.browse(cr, uid, ids, context=context):
            if move_line.journal_id.posting_policy == 'storno':
                if move_line.debit < 0 or move_line.credit < 0:
                    res[move_line.id]['amount_residual_currency'] = res[
                        move_line.id]['amount_residual_currency'] * (-1)
                    res[move_line.id]['amount_residual'] = res[
                        move_line.id]['amount_residual'] * (-1)
        return res

    _columns = {
        'amount_residual_currency': fields.function(
            _amount_residual,
            string='Residual Amount in Currency',
            multi="residual",
            help="The residual amount on a receivable or payable of a journal "
                 "entry expressed in its currency (maybe different of the "
                 "company currency)."),
        'amount_residual': fields.function(
            _amount_residual,
            string='Residual Amount',
            multi="residual",
            help="The residual amount on a receivable or payable of a journal "
                 "entry expressed in the company currency."),
    }


class account_model_line(orm.Model):
    _inherit = "account.model.line"

    def _auto_init(self, cr, context=None):
        result = super(account_model_line, self)._auto_init(cr,
                                                            context=context)
        # Drop original constraint to fit storno posting with minus.
        cr.execute("""
            DROP INDEX IF EXISTS account_model_line_credit_debit2;
        """)
        return result

    # Original constraints
    # 'credit_debit2' - 'CHECK (credit+debit>=0)' is replaced with dummy
    # constraint that is always true.

    _sql_constraints = [
        ('credit_debit2',
         'CHECK (abs(credit+debit)>=0)',
         'Wrong credit or debit value in accounting entry !'),
    ]
