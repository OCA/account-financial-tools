# -*- coding: utf-8 -*-
# Copyright 2011 Akretion (http://www.akretion.com). All Rights Reserved
# Copyright 2012-2013 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp.models import api, fields, models, _
from openerp.exceptions import ValidationError, MissingError


class AccountMoveReversal(models.TransientModel):
    _name = "account.move.reverse"
    _description = "Create reversal of account moves"

    def _next_period_first_date(self):
        res = False
        period_ctx = self.env.context
        period_ctx['account_period_prefer_normal'] = True
        period_obj = self.env['account.period']
        if self.env.context.get('active_model') != 'account.move':
            raise ValidationError(_('Active model != account.move'))
        to_reverse_move = self.env['account.move'].browse(
            self.env.context['active_id'])
        next_period_id = period_obj.next(
            to_reverse_move.period_id, 1)
        if next_period_id:
            next_period = period_obj.browse(next_period_id)
            res = next_period.date_start
        return res

    date = fields.Date(
        'Reversal Date',
        required=True,
        help="Enter the date of the reversal account entries. "
             "By default, OpenERP proposes the first day of "
             "the period following the period of the move to reverse.",
        default=_next_period_first_date,
    )
    period_id = fields.Many2one(
        'account.period',
        'Reversal Period',
        help="If empty, take the period of the date.",
    )
    journal_id = fields.Many2one(
        'account.journal',
        'Reversal Journal',
        help='If empty, uses the journal of the journal entry '
             'to be reversed.',
    )
    move_prefix = fields.Char(
        'Entries Ref. Prefix',
        help="Prefix that will be added to the 'Ref' of the journal "
             "entry to be reversed to create the 'Ref' of the "
             "reversal journal entry (no space added after the prefix).",
    )
    move_line_prefix = fields.Char(
        'Items Name Prefix',
        help="Prefix that will be added to the name of the journal "
             "item to be reversed to create the name of the reversal "
             "journal item (a space is added after the prefix).",
        default='REV -',
    )
    reconcile = fields.Boolean('Reconcile')

    @api.multi
    def action_reverse(self):
        move_ids = self.env.context.get('active_ids')
        if not move_ids:
            raise MissingError(_('active_ids missing in context.'))
        form = self.read()
        move_obj = self.env['account.move']
        period_id = form['period_id'][0] if form.get('period_id') else False
        journal_id = form['journal_id'][0] if form.get('journal_id') else False
        reconcile = form['reconcile'] if form.get('reconcile') else False
        reversed_move_ids = move_obj.create_reversals(
            move_ids,
            form['date'],
            reversal_period_id=period_id,
            reversal_journal_id=journal_id,
            move_prefix=form['move_prefix'],
            move_line_prefix=form['move_line_prefix'],
            reconcile=reconcile,
        )
        action = self.env['ir.actions.act_window'].for_xml_id(
            'account',
            'action_move_journal_line',
        )
        action['name'] = _('Reversal Entries')
        action['context'] = unicode({'search_default_to_be_reversed': 0})
        if len(reversed_move_ids) == 1:
            action['res_id'] = reversed_move_ids[0]
            action['view_mode'] = 'form,tree'
            action['views'] = False
            action['view_id'] = False
        else:
            action['domain'] = unicode([('id', 'in', reversed_move_ids)])
        return action
