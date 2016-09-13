# -*- coding: utf-8 -*-
##############################################################################
#
#    Account reversal module for OpenERP
#    Copyright (C) 2011 Akretion (http://www.akretion.com). All Rights Reserved
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    with the kind advice of Nicolas Bessi from Camptocamp
#    Copyright (C) 2012-2013 Camptocamp SA (http://www.camptocamp.com)
#    @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
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

from openerp import fields, models, api, _


class account_move(models.Model):
    _inherit = "account.move"

    to_be_reversed = fields.Boolean(
        'To Be Reversed',
        help='Check this box if your entry has to be'
        'reversed at the end of period.')
    reversal_id = fields.Many2one(
        'account.move',
        'Reversal Entry',
        ondelete='set null',
        readonly=True)

    @api.multi
    def validate(self):
        # TODO: remove this method if and when
        #       https://github.com/odoo/odoo/pull/7735 is merged
        if self.env.context.get('novalidate'):
            return
        return super(account_move, self).validate()

    @api.multi
    def _move_reversal(self, reversal_date,
                       reversal_period_id=False, reversal_journal_id=False,
                       move_prefix=False, move_line_prefix=False,
                       reconcile=False):
        """
        Create the reversal of a move

        :param move: browse instance of the move to reverse
        :param reversal_date: when the reversal must be input
        :param reversal_period_id: facultative period to write on the move
                                   (use the period of the date if empty
        :param reversal_journal_id: facultative journal on which create
                                    the move
        :param move_prefix: prefix for the move's name
        :param move_line_prefix: prefix for the move line's names

        :return: Returns the id of the created reversal move
        """
        self.ensure_one()
        period_obj = self.env['account.period']
        amlo = self.env['account.move.line']

        if reversal_period_id:
            reversal_period = period_obj.browse([reversal_period_id])[0]
        else:
            reversal_period = period_obj.with_context(
                company_id=self.company_id.id,
                account_period_prefer_normal=True).find(reversal_date)[0]
        if not reversal_journal_id:
            reversal_journal_id = self.journal_id.id

        if self.env['account.journal'].browse([
                reversal_journal_id]).company_id != self.company_id:
            raise Warning(_('Wrong company Journal is %s but we have %s') % (
                reversal_journal_id.company_id.name, self.company_id.name))
        if reversal_period.company_id != self.company_id:
            raise Warning(_('Wrong company Period is %s but we have %s') % (
                reversal_journal_id.company_id.name, self.company_id.name))

        reversal_ref = ''.join([x for x in [move_prefix, self.ref] if x])
        reversal_move = self.copy(default={
            'company_id': self.company_id.id,
            'date': reversal_date,
            'period_id': reversal_period.id,
            'ref': reversal_ref,
            'journal_id': reversal_journal_id,
            'to_be_reversed': False,
        })

        self.with_context(novalidate=True).write({
            'reversal_id': reversal_move.id,
            'to_be_reversed': False,
        })

        rec_dict = {}
        for rev_move_line in reversal_move.line_id:
            rev_ml_name = ' '.join(
                [x for x
                 in [move_line_prefix, rev_move_line.name]
                 if x]
            )
            rev_move_line.write(
                {'debit': rev_move_line.credit,
                 'credit': rev_move_line.debit,
                 'amount_currency': rev_move_line.amount_currency * -1,
                 'name': rev_ml_name},
                check=True,
                update_check=True)

            if reconcile and rev_move_line.account_id.reconcile:
                rec_dict.setdefault(
                    (rev_move_line.account_id, rev_move_line.partner_id),
                    amlo.browse(False))
                rec_dict[(rev_move_line.account_id, rev_move_line.partner_id)]\
                    += rev_move_line

        reversal_move.validate()
        if reconcile:
            for mline in self.line_id:
                if mline.account_id.reconcile:
                    rec_dict[(mline.account_id, mline.partner_id)] += mline

            for to_rec_move_lines in rec_dict.itervalues():
                to_rec_move_lines.reconcile()

        return reversal_move.id

    @api.multi
    def create_reversals(self, reversal_date, reversal_period_id=False,
                         reversal_journal_id=False,
                         move_prefix=False, move_line_prefix=False,
                         reconcile=False):
        """
        Create the reversal of one or multiple moves

        :param reversal_date: when the reversal must be input
        :param reversal_period_id: facultative period to write on the move
                                   (use the period of the date if empty
        :param reversal_journal_id: facultative journal on which create
                                    the move
        :param move_prefix: prefix for the move's name
        :param move_line_prefix: prefix for the move line's names

        :return: Returns a list of ids of the created reversal moves
        """
        return [
            move._move_reversal(
                reversal_date,
                reversal_period_id=reversal_period_id,
                reversal_journal_id=reversal_journal_id,
                move_prefix=move_prefix,
                move_line_prefix=move_line_prefix,
                reconcile=reconcile
            )
            for move in self
            if not move.reversal_id
        ]
